from django.shortcuts import render
import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Prefetch,Case,When,Value,DecimalField
from django.shortcuts import get_object_or_404,render
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView,ListView
from rest_framework.decorators import api_view
from django.core.cache import cache
from .pagination import StandardResultsSetPagination

from django.db.models.signals import post_save, post_delete

from .models import (
    User, OTP, Address, Category, Brand, Product, ProductImage,
    ProductVariation, Cart, CartItem, Order, OrderItem, Payment,
    OrderTracking, Wishlist, RecentlyViewed, Review
)
from .serializers import (
    UserSerializer, OTPSerializer, AddressSerializer, CategorySerializer,
    BrandSerializer, ProductSerializer, ProductDetailSerializer, CartSerializer,
    CartItemSerializer, OrderSerializer, OrderDetailSerializer, PaymentSerializer,
    WishlistSerializer, ReviewSerializer, RecentlyViewedSerializer
)
from .filters import ProductFilter

from .cache_utils import (
    get_all_products_cached,
    get_featured_products_cached,
    get_new_arrivals_cached,
    get_top_selling_products_cached,
    get_active_categories_cached,
    get_active_brands_cached,
    get_price_range_cached,
    CacheKeys,
    CacheManager,
)


import json
import hashlib
from django.db.models import Prefetch
CACHE_TIMEOUT = 3600
NEW_PRODUCT_DAYS = 7 

class ProductsView(TemplateView):
    template_name = "pages/sample.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all products with caching
        context['products'] = self._get_cached_products()
        
        # Get filter options
        context['categories'] = self._get_cached_categories()
        context['brands'] = self._get_cached_brands()
        context['price_range'] = self._get_price_range()
        
        return context
    
    def _get_cached_products(self):
        """Get all products with efficient caching"""
        cache_key = 'all_products'
        products = cache.get(cache_key)
        
        if products is None:
            primary_image_qs = ProductImage.objects.filter(is_primary=True)
            new_date = timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)
            
            products = Product.objects.filter(is_active=True).select_related(
                "category", "brand"
            ).prefetch_related(
                Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
            ).annotate(
                is_new=Case(
                    When(created_at__gte=new_date, then=Value(True)),
                    default=Value(False)
                ),
                discount_price=Case(
                    When(compare_price__gt=F('price'), then=F('compare_price')),
                    default=F('price'),
                    output_field=DecimalField()
                )
            ).values(
                'id', 'name', 'slug', 'price', 'compare_price', 'is_featured',
                'is_new', 'views_count', 'sales_count', 'stock',
                'category__id', 'category__name', 'brand__id', 'brand__name'
            ).order_by('-is_featured', '-sales_count', '-created_at')
            
            cache.set(cache_key, list(products), CACHE_TIMEOUT)
            return list(products)
        
        return products
    
    def _get_cached_categories(self):
        """Get active categories with caching"""
        cache_key = 'active_categories'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = Category.objects.filter(
                is_active=True, parent=None
            ).prefetch_related('children').values(
                'id', 'name', 'slug'
            )
            cache.set(cache_key, list(categories), CACHE_TIMEOUT)
            return list(categories)
        
        return categories
    
    def _get_cached_brands(self):
        """Get active brands with caching"""
        cache_key = 'active_brands'
        brands = cache.get(cache_key)
        
        if brands is None:
            brands = Brand.objects.filter(
                is_active=True
            ).annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            ).filter(
                product_count__gt=0
            ).values('id', 'name', 'slug', 'product_count').order_by('name')
            
            cache.set(cache_key, list(brands), CACHE_TIMEOUT)
            return list(brands)
        
        return brands
    
    def _get_price_range(self):
        """Get min and max product prices"""
        cache_key = 'product_price_range'
        price_range = cache.get(cache_key)
        
        if price_range is None:
            from django.db.models import Min, Max
            
            price_stats = Product.objects.filter(
                is_active=True
            ).aggregate(
                min_price=Min(Case(
                    When(compare_price__gt=0, then='compare_price'),
                    default='price'
                )),
                max_price=Max('price')
            )
            price_range = {
                'min': int(price_stats['min_price'] or 0),
                'max': int(price_stats['max_price'] or 0)
            }
            cache.set(cache_key, price_range, CACHE_TIMEOUT)
        
        return price_range


@api_view(['GET'])
def get_filtered_products(request):
    """API endpoint for AJAX product filtering with caching"""
    
    # Get filter parameters
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    tab = request.GET.get('tab', 'all')
    search = request.GET.get('search', '')
    min_price = request.GET.getint('min_price', 0)
    max_price = request.GET.getint('max_price', 999999)
    sort = request.GET.get('sort', '-is_featured')
    
    # Generate cache key from parameters
    cache_params = f"{category_id}_{brand_id}_{tab}_{search}_{min_price}_{max_price}_{sort}"
    cache_key = f"filtered_products_{hashlib.md5(cache_params.encode()).hexdigest()}"
    
    cached_products = cache.get(cache_key)
    if cached_products is not None:
        return Response({'products': cached_products})
    
    # Build query
    queryset = Product.objects.filter(is_active=True)
    
    new_date = timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)
    
    # Apply filters based on tab
    if tab == 'new':
        queryset = queryset.filter(created_at__gte=new_date)
    elif tab == 'featured':
        queryset = queryset.filter(is_featured=True)
    elif tab == 'sale':
        queryset = queryset.filter(compare_price__gt=F('price'))
    elif tab == 'top_selling':
        queryset = queryset.filter(sales_count__gt=0)
    
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    if brand_id:
        queryset = queryset.filter(brand_id=brand_id)
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search) |
            Q(short_description__icontains=search) | Q(sku__icontains=search)
        )
    
    # Price filter - use compare_price if available, else use price
    queryset = queryset.annotate(
        sale_price=Case(
            When(compare_price__gt=0, then='compare_price'),
            default='price',
            output_field=DecimalField()
        ),
        is_new=Case(
            When(created_at__gte=new_date, then=Value(True)),
            default=Value(False)
        )
    ).filter(sale_price__gte=min_price, sale_price__lte=max_price)
    
    # Optimize query
    primary_image_qs = ProductImage.objects.filter(is_primary=True)
    
    # Determine sort order
    if sort == '-sales_count':
        products = queryset.select_related(
            "category", "brand"
        ).prefetch_related(
            Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
        ).order_by('-sales_count', '-created_at').values(
            'id', 'name', 'slug', 'price', 'compare_price',
            'is_featured', 'stock', 'sales_count', 'category__name',
            'brand__name'
        )[:100]
    else:
        products = queryset.select_related(
            "category", "brand"
        ).prefetch_related(
            Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
        ).order_by('-is_featured', '-sales_count', '-created_at').values(
            'id', 'name', 'slug', 'price', 'compare_price',
            'is_featured', 'stock', 'sales_count', 'category__name',
            'brand__name'
        )[:100]
    
    products_list = list(products)
    
    # Cache the results
    cache.set(cache_key, products_list, CACHE_TIMEOUT)
    
    return Response({'products': products_list})


class HomeView(TemplateView):
    template_name = "index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured products with cache
        context['featured_products'] = self._get_featured_products()
        
        # New arrivals with cache
        context['new_arrivals'] = self._get_new_arrivals()
        
        # Top selling with cache
        context['top_selling'] = self._get_top_selling()
        
        # Categories for mega menu
        context['categories'] = self._get_cached_categories()
        
        return context
    
    def _get_featured_products(self):
        """Get featured products with caching"""
        cache_key = 'featured_products_home'
        featured = cache.get(cache_key)
        
        if featured is None:
            primary_image_qs = ProductImage.objects.filter(is_primary=True)
            featured = list(
                Product.objects.filter(is_active=True, is_featured=True)
                .select_related("category", "brand")
                .prefetch_related(
                    Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
                ).order_by('-created_at')[:8]
            )
            cache.set(cache_key, featured, CACHE_TIMEOUT)
        
        return featured
    
    def _get_new_arrivals(self):
        """Get new arrival products with caching"""
        cache_key = 'new_arrivals_home'
        new = cache.get(cache_key)
        
        if new is None:
            new_date = timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)
            primary_image_qs = ProductImage.objects.filter(is_primary=True)
            new = list(
                Product.objects.filter(is_active=True, created_at__gte=new_date)
                .select_related("category", "brand")
                .prefetch_related(
                    Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
                ).order_by('-created_at')[:8]
            )
            cache.set(cache_key, new, CACHE_TIMEOUT)
        
        return new
    
    def _get_top_selling(self):
        """Get top selling products with caching"""
        cache_key = 'top_selling_home'
        top = cache.get(cache_key)
        
        if top is None:
            primary_image_qs = ProductImage.objects.filter(is_primary=True)
            top = list(
                Product.objects.filter(is_active=True, sales_count__gt=0)
                .select_related("category", "brand")
                .prefetch_related(
                    Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
                ).order_by('-sales_count', '-created_at')[:8]
            )
            cache.set(cache_key, top, CACHE_TIMEOUT)
        
        return top
    
    def _get_cached_categories(self):
        """Get categories with caching"""
        cache_key = 'categories_mega_menu'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(
                Category.objects.filter(is_active=True, parent=None)
                .prefetch_related('children')[:4]
            )
            cache.set(cache_key, categories, CACHE_TIMEOUT)
        
        return categories
# ==================== Authentication Views ====================
class SendOTPView(APIView):
    """Send OTP to mobile number"""
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        if not mobile:
            return Response({'error': 'Mobile number is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # Invalidate previous OTPs
        OTP.objects.filter(mobile=mobile, is_verified=False).update(is_verified=True)

        # Create new OTP
        otp = OTP.objects.create(
            mobile=mobile,
            otp=otp_code,
            expires_at=expires_at
        )

        # TODO: Send OTP via SMS gateway (Twilio, MSG91, etc.)
        # For development, return OTP in response
        return Response({
            'message': 'OTP sent successfully',
            'otp': otp_code,  # Remove in production
            'mobile': mobile
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """Verify OTP and login/register user"""
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        otp_code = request.data.get('otp')

        if not mobile or not otp_code:
            return Response({'error': 'Mobile and OTP are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = OTP.objects.get(mobile=mobile, otp=otp_code, is_verified=False)
            
            if not otp.is_valid():
                return Response({'error': 'OTP expired or invalid'}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as verified
            otp.is_verified = True
            otp.save()

            # Get or create user
            user, created = User.objects.get_or_create(
                mobile=mobile,
                defaults={'username': mobile, 'is_mobile_verified': True}
            )

            if not created and not user.is_mobile_verified:
                user.is_mobile_verified = True
                user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'is_new_user': created,
                'profile_completed': user.profile_completed,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except OTP.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout user"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, 
                          status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CompleteProfileView(APIView):
    """Complete user profile"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.date_of_birth = request.data.get('date_of_birth', user.date_of_birth)
        user.gender = request.data.get('gender', user.gender)
        user.profile_completed = True
        user.save()

        return Response({
            'message': 'Profile completed successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# ==================== Address Views ====================
class AddressListCreateView(generics.ListCreateAPIView):
    """List and create addresses"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete address"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class SetDefaultAddressView(APIView):
    """Set address as default"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        Address.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated'}, 
                       status=status.HTTP_200_OK)


# ==================== Product Views ====================
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Product ViewSet"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'sales_count', 'views_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        ).prefetch_related('images', 'variations')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail by slug"""
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        ).prefetch_related('images', 'variations', 'reviews')


class FeaturedProductsView(generics.ListAPIView):
    """Featured products"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, is_featured=True
        ).order_by('-created_at')


class TrendingProductsView(generics.ListAPIView):
    """Trending products based on sales"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by('-sales_count')[:20]


class ProductSearchView(generics.ListAPIView):
    """Product search"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        return Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query),
            is_active=True
        ).distinct()


class TrackProductViewView(APIView):
    """Track product view and add to recently viewed"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        
        # Increment view count
        product.views_count = F('views_count') + 1
        product.save(update_fields=['views_count'])
        
        # Add to recently viewed
        RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product
        )
        
        return Response({'message': 'View tracked'}, status=status.HTTP_200_OK)


# ==================== Category Views ====================
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Category ViewSet"""
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related('children')


class CategoryTreeView(APIView):
    """Get category tree structure"""
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.filter(is_active=True, parent=None)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CategoryProductsView(generics.ListAPIView):
    """Products by category"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        category = get_object_or_404(Category, slug=slug, is_active=True)
        
        # Get all child categories
        categories = [category]
        categories.extend(category.children.filter(is_active=True))
        
        return Product.objects.filter(
            category__in=categories, is_active=True
        ).order_by('-created_at')


# ==================== Brand Views ====================
class BrandListView(generics.ListAPIView):
    """List all brands"""
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(is_active=True)


class BrandProductsView(generics.ListAPIView):
    """Products by brand"""
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        brand = get_object_or_404(Brand, slug=slug, is_active=True)
        return Product.objects.filter(brand=brand, is_active=True).order_by('-created_at')


# ==================== Cart Views ====================
class CartViewSet(viewsets.ModelViewSet):
    """Cart ViewSet"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items')


class CartDetailView(APIView):
    """Get cart details"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    """Add item to cart"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        variation_id = request.data.get('variation_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id, is_active=True)
        variation = None
        
        if variation_id:
            variation = get_object_or_404(ProductVariation, pk=variation_id, product=product)

        # Check stock
        available_stock = variation.stock if variation else product.stock
        if quantity > available_stock:
            return Response({'error': 'Insufficient stock'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Calculate price
        price = product.price
        if variation and variation.price_adjustment:
            price += variation.price_adjustment

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variation=variation,
            defaults={'quantity': quantity, 'price': price}
        )

        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > available_stock:
                return Response({'error': 'Insufficient stock'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            cart_item.save()

        return Response({
            'message': 'Item added to cart',
            'cart': CartSerializer(cart).data
        }, status=status.HTTP_200_OK)


class UpdateCartItemView(APIView):
    """Update cart item quantity"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        quantity = int(request.data.get('quantity', 1))

        if quantity <= 0:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'}, 
                          status=status.HTTP_200_OK)

        # Check stock
        available_stock = cart_item.variation.stock if cart_item.variation else cart_item.product.stock
        if quantity > available_stock:
            return Response({'error': 'Insufficient stock'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            'message': 'Cart updated',
            'cart': CartSerializer(cart_item.cart).data
        }, status=status.HTTP_200_OK)


class RemoveCartItemView(APIView):
    """Remove item from cart"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        cart_item.delete()
        return Response({'message': 'Item removed from cart'}, 
                       status=status.HTTP_200_OK)


class ClearCartView(APIView):
    """Clear entire cart"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)


# ==================== Wishlist Views ====================
class WishlistViewSet(viewsets.ModelViewSet):
    """Wishlist ViewSet"""
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')


class WishlistListView(generics.ListAPIView):
    """List wishlist items"""
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')


class AddToWishlistView(APIView):
    """Add to wishlist"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({'message': 'Added to wishlist'}, 
                          status=status.HTTP_201_CREATED)
        return Response({'message': 'Already in wishlist'}, 
                       status=status.HTTP_200_OK)


class RemoveFromWishlistView(APIView):
    """Remove from wishlist"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        wishlist = get_object_or_404(Wishlist, pk=pk, user=request.user)
        wishlist.delete()
        return Response({'message': 'Removed from wishlist'}, 
                       status=status.HTTP_200_OK)


# ==================== Order Views ====================
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Order ViewSet"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer


class OrderListView(generics.ListAPIView):
    """List user orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """Order detail"""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items', 'payments', 'tracking'
        )


class CreateOrderView(APIView):
    """Create order from cart"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        shipping_address_id = request.data.get('shipping_address_id')
        shipping_address = get_object_or_404(Address, pk=shipping_address_id, user=user)
        
        billing_address_id = request.data.get('billing_address_id', shipping_address_id)
        billing_address = get_object_or_404(Address, pk=billing_address_id, user=user)

        # Calculate totals
        subtotal = cart.subtotal
        tax_amount = subtotal * 0.18  # 18% tax
        shipping_charge = 0 if subtotal > 500 else 50
        total_amount = subtotal + tax_amount + shipping_charge

        # Create order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            billing_address=billing_address,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_charge=shipping_charge,
            total_amount=total_amount
        )

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variation=cart_item.variation,
                product_name=cart_item.product.name,
                sku=cart_item.product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.price,
                total_price=cart_item.total_price
            )

        # Create order tracking
        OrderTracking.objects.create(
            order=order,
            status='pending',
            message='Order placed successfully'
        )

        # Clear cart
        cart.items.all().delete()

        return Response({
            'message': 'Order created successfully',
            'order': OrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
    """Cancel order"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        
        if order.status not in ['pending', 'confirmed']:
            return Response({'error': 'Cannot cancel this order'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.cancellation_reason = request.data.get('reason', '')
        order.save()

        # Create tracking entry
        OrderTracking.objects.create(
            order=order,
            status='cancelled',
            message=f'Order cancelled: {order.cancellation_reason}'
        )

        return Response({'message': 'Order cancelled successfully'}, 
                       status=status.HTTP_200_OK)


class OrderTrackingView(APIView):
    """Get order tracking history"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        tracking = order.tracking.all().order_by('-created_at')
        
        tracking_data = [{
            'status': t.status,
            'message': t.message,
            'location': t.location,
            'timestamp': t.created_at
        } for t in tracking]
        
        return Response(tracking_data, status=status.HTTP_200_OK)


# ==================== Payment Views ====================
class InitiatePaymentView(APIView):
    """Initiate payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        payment_method = request.data.get('payment_method', 'cod')
        
        order = get_object_or_404(Order, pk=order_id, user=request.user)

        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=order.total_amount,
            status='pending'
        )

        if payment_method == 'cod':
            payment.status = 'completed'
            payment.save()
            
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.save()
            
            OrderTracking.objects.create(
                order=order,
                status='confirmed',
                message='Order confirmed - Cash on Delivery'
            )

        # TODO: Integrate payment gateway (Razorpay, Stripe, etc.)
        
        return Response({
            'message': 'Payment initiated',
            'payment': PaymentSerializer(payment).data
        }, status=status.HTTP_200_OK)


class VerifyPaymentView(APIView):
    """Verify payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        transaction_id = request.data.get('transaction_id')
        
        payment = get_object_or_404(Payment, pk=payment_id)
        
        # TODO: Verify with payment gateway
        
        payment.status = 'completed'
        payment.transaction_id = transaction_id
        payment.save()
        
        order = payment.order
        order.status = 'confirmed'
        order.confirmed_at = timezone.now()
        order.save()
        
        OrderTracking.objects.create(
            order=order,
            status='confirmed',
            message='Payment successful - Order confirmed'
        )
        
        return Response({'message': 'Payment verified'}, 
                       status=status.HTTP_200_OK)


class PaymentCallbackView(APIView):
    """Payment gateway callback"""
    permission_classes = [AllowAny]

    def post(self, request):
        # TODO: Handle payment gateway callback
        return Response({'message': 'Callback received'}, 
                       status=status.HTTP_200_OK)


# ==================== Review Views ====================
class ReviewViewSet(viewsets.ModelViewSet):
    """Review ViewSet"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


class ProductReviewsView(generics.ListAPIView):
    """Get product reviews"""
    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Review.objects.filter(
            product_id=product_id, is_approved=True
        ).order_by('-created_at')


class CreateReviewView(APIView):
    """Create product review"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        rating = int(request.data.get('rating'))
        title = request.data.get('title')
        comment = request.data.get('comment')
        
        product = get_object_or_404(Product, pk=product_id)
        
        # Check if already reviewed
        if Review.objects.filter(user=request.user, product=product).exists():
            return Response({'error': 'Already reviewed'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Check if purchased
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()

        review = Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            title=title,
            comment=comment,
            is_verified_purchase=has_purchased
        )

        return Response({
            'message': 'Review submitted',
            'review': ReviewSerializer(review).data
        }, status=status.HTTP_201_CREATED)


class MarkReviewHelpfulView(APIView):
    """Mark review as helpful"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.helpful_count = F('helpful_count') + 1
        review.save(update_fields=['helpful_count'])
        return Response({'message': 'Marked as helpful'}, 
                       status=status.HTTP_200_OK)


# ==================== User Activity Views ====================
class RecentlyViewedView(generics.ListAPIView):
    """Recently viewed products"""
    serializer_class = RecentlyViewedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecentlyViewed.objects.filter(
            user=self.request.user
        ).select_related('product').order_by('-viewed_at')[:20]


class UserDashboardView(APIView):
    """User dashboard with statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        orders = Order.objects.filter(user=user)
        
        dashboard_data = {
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='pending').count(),
            'completed_orders': orders.filter(status='delivered').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
            'total_spent': orders.filter(status='delivered').aggregate(
                total=Sum('total_amount'))['total'] or 0,
            'wishlist_count': Wishlist.objects.filter(user=user).count(),
            'cart_items': Cart.objects.filter(user=user).first().total_items if hasattr(user, 'cart') else 0,
            'profile_completed': user.profile_completed,
            'recent_orders': OrderSerializer(
                orders.order_by('-created_at')[:5], many=True
            ).data
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)