from django.shortcuts import render
import random
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Prefetch,Case,When,Value,DecimalField
from django.shortcuts import get_object_or_404,render,redirect
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
import json
import hashlib
from django.contrib.auth import get_user_model
from django.contrib.auth import login,logout

from django.contrib import messages


from django.db.models.signals import post_save, post_delete


from .tasks import send_otp_sms_task


from .models import (
    User, OTP, Address, Category, Brand, Product, ProductImage,
    ProductVariation, Cart, CartItem, Order, OrderItem, Payment,
    OrderTracking, Wishlist, RecentlyViewed, Review,ContactMessage
)

from .forms import OTPRequestForm ,OTPVerifyForm,ContactForm
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
    get_mega_menu_categories_cached,
    CacheKeys,
    CacheManager,
    NEW_PRODUCT_DAYS,
)


from django.conf import settings



CACHE_TIMEOUT = 3600
NEW_PRODUCT_DAYS = 7 

User = get_user_model()




# Views
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Here you can:
            # 1. Save to database
            # 2. Send email notification
            # 3. Log the contact request
            
            # Example: Save to database (you'll need to create a ContactMessage model)
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            
            # Show success message
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'pages/contact.html', {'form': form})

def about_view(request):
    return render(request, 'pages/about.html')

def privacy_policy_view(request):
    return render(request, 'pages/privacy_policy.html')

def terms_conditions_view(request):
    return render(request, 'pages/terms_conditions.html')

def return_policy_view(request):
    return render(request, 'pages/return_policy.html')




class ProductsView(TemplateView):
    template_name = "pages/sample.html"
    CACHE_TIMEOUT = 3600

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cache key
        cache_key = "all_products_with_primary_images"
        products = cache.get(cache_key)

        if products is None:
            primary_image_qs = ProductImage.objects.filter(is_primary=True)

            products = (
                Product.objects.filter(is_active=True)
                .select_related("category", "brand")
                .prefetch_related(
                    Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
                )
            )

            # Cache product queryset as list to avoid QuerySet re-evaluation
            cache.set(cache_key, list(products), self.CACHE_TIMEOUT)

        context['products'] = products

        # Other cached filters
        context['categories'] = get_active_categories_cached()
        context['brands'] = get_active_brands_cached()
        context['price_range'] = get_price_range_cached()

        return context


@api_view(['GET'])
def get_filtered_products(request):
    """API endpoint for AJAX product filtering with caching"""
    
    # Get filter parameters
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    tab = request.GET.get('tab', 'all')
    search = request.GET.get('search', '')
    min_price = int(request.GET.get('min_price', 0))
    max_price = int(request.GET.get('max_price', 999999))
    sort = request.GET.get('sort', '-is_featured')
    
    # Generate cache key from parameters
    cache_key = CacheKeys.filtered_products_key(
        category_id, brand_id, tab, search, min_price, max_price, sort
    )
    
    # Check cache first
    cached_products = CacheManager.get(cache_key)
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
    
    # Price filter
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
    
    # Optimize query with prefetch
    primary_image_qs = ProductImage.objects.filter(is_primary=True)
    
    # Determine sort order
    if sort == '-sales_count':
        order_by = ['-sales_count', '-created_at']
    elif sort == 'price':
        order_by = ['price']
    elif sort == '-price':
        order_by = ['-price']
    elif sort == 'name':
        order_by = ['name']
    else:
        order_by = ['-is_featured', '-sales_count', '-created_at']
    
    # Fetch products (as objects, not values)
    products = queryset.select_related(
        "category", "brand"
    ).prefetch_related(
        Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
    ).order_by(*order_by)[:100]
    
    # Serialize products manually for API response
    products_list = []
    for product in products:
        # Get primary image URL
        primary_image = None
        if hasattr(product, 'primary_images') and product.primary_images:
            primary_image = product.primary_images[0].image.url
        
        products_list.append({
            'id': str(product.id),
            'name': product.name,
            'slug': product.slug,
            'price': str(product.price),
            'compare_price': str(product.compare_price) if product.compare_price else None,
            'is_featured': product.is_featured,
            'stock': product.stock,
            'sales_count': product.sales_count,
            'category_name': product.category.name if product.category else None,
            'brand_name': product.brand.name if product.brand else None,
            'primary_image': primary_image,
            'discount_percentage': product.discount_percentage,
            'is_low_stock': product.is_low_stock,
        })
    
    # Cache the results
    CacheManager.set(cache_key, products_list)
    
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


class AuthPageView(TemplateView):
    template_name = "auth.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mobile_form"] = OTPRequestForm()
        ctx["otp_form"] = OTPVerifyForm()
        return ctx

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get("mobile")
        if not mobile:
            return Response({"error": "Mobile number is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # Invalidate previous unverified OTPs
        OTP.objects.filter(mobile=mobile, is_verified=False).update(is_verified=True)

        # Store hashed OTP
        OTP.create_otp(mobile, otp_code, expires_at)

        # Send SMS async using Celery
        send_otp_sms_task.delay(mobile, otp_code)

        return Response({
            "message": "OTP sent successfully",
            "mobile": mobile,
            # "otp": otp_code  # For debugging (remove in prod)
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get("mobile")
        raw_otp = request.data.get("otp")

        if not mobile or not raw_otp:
            return Response({"error": "Mobile and OTP are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get latest OTP
        otps = OTP.objects.filter(mobile=mobile, is_verified=False).order_by("-created_at")
        if not otps.exists():
            return Response({"error": "Invalid or expired OTP"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        otp_obj = otps.first()

        if not otp_obj.is_valid(raw_otp):
            return Response({"error": "Invalid OTP"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Mark as verified
        otp_obj.is_verified = True
        otp_obj.save()

        # Create or fetch user
        user, created = User.objects.get_or_create(
            mobile=mobile,
            defaults={"username": mobile, "is_mobile_verified": True}
        )

        if not user.is_mobile_verified:
            user.is_mobile_verified = True
            user.save()

        # JWT token generation
        refresh = RefreshToken.for_user(user)
        login(request, user)  

        return Response({
            "message": "Login successful",
            "is_new_user": created,
            "profile_completed": user.profile_completed,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout user"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            logout(request) 
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


# class CategoryTreeView(APIView):
#     """Get category tree structure"""
#     permission_classes = [AllowAny]

#     def get(self, request):
#         categories = Category.objects.filter(is_active=True, parent=None)
#         serializer = CategorySerializer(categories, many=True)
#         return Response(serializer.data)


class CategoryProductsView(ListView):
    template_name = "pages/category_page.html"
    context_object_name = "products"
    paginate_by = 10

    def get_category(self):
        slug = self.kwargs["slug"]
        key = f"category_obj_{slug}"

        category = cache.get(key)
        if not category:
            category = get_object_or_404(
                Category.objects.filter(is_active=True)
                .prefetch_related("children"),
                slug=slug
            )
            cache.set(key, category, 60 * 60)
        return category

    def get_queryset(self):
        category = self.get_category()
        key = f"category_products_{category.slug}"

        products = cache.get(key)
        if not products:
            categories = [category] + list(category.children.filter(is_active=True))
            products = (
                Product.objects.filter(category__in=categories, is_active=True)
                .select_related("category", "brand")
                .prefetch_related("images")
                .order_by("-created_at")
            )
            cache.set(key, products, 60 * 60)
        return products

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        category = self.get_category()
        ctx["category"] = category
        return ctx

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