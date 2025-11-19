
from rest_framework import serializers
from django.db.models import Avg
from .models import (
    User, OTP, Address, Category, Brand, Product, ProductImage,
    ProductVariation, Cart, CartItem, Order, OrderItem, Payment,
    OrderTracking, Wishlist, RecentlyViewed, Review, ReviewImage
)


# ==================== User Serializers ====================
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'mobile', 'username', 'email', 'first_name', 'last_name',
                 'full_name', 'date_of_birth', 'gender', 'is_mobile_verified',
                 'profile_completed', 'created_at']
        read_only_fields = ['id', 'is_mobile_verified', 'created_at']

    def get_full_name(self, obj):
        return obj.get_full_name() or ''


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'mobile', 'otp', 'is_verified', 'created_at', 'expires_at']
        read_only_fields = ['id', 'created_at']


# ==================== Address Serializers ====================
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_type', 'full_name', 'mobile', 'pincode',
                 'address_line1', 'address_line2', 'landmark', 'city', 'state',
                 'country', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ==================== Category Serializers ====================
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'parent',
                 'children', 'product_count', 'is_active', 'display_order']
        read_only_fields = ['id']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


# ==================== Brand Serializers ====================
class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'is_active', 'product_count']
        read_only_fields = ['id']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


# ==================== Product Serializers ====================
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'display_order']
        read_only_fields = ['id']


class ProductVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariation
        fields = ['id', 'variation_type', 'variation_value', 'price_adjustment',
                 'stock', 'sku_suffix', 'is_active']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'sku', 'category', 'category_name',
                 'brand', 'brand_name', 'short_description', 'price',
                 'compare_price', 'discount_percentage', 'stock', 'is_active',
                 'is_featured', 'primary_image', 'average_rating', 'review_count',
                 'sales_count', 'views_count', 'created_at']
        read_only_fields = ['id', 'sales_count', 'views_count', 'created_at']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url if primary.image else None
        first_image = obj.images.first()
        return first_image.image.url if first_image and first_image.image else None

    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


class ProductDetailSerializer(ProductSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    brand_detail = BrandSerializer(source='brand', read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + [
            'description', 'cost_price', 'low_stock_threshold',
            'images', 'variations', 'category_detail', 'brand_detail',
            'meta_title', 'meta_description'
        ]


# ==================== Cart Serializers ====================
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    variation_details = ProductVariationSerializer(source='variation', read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_image', 'variation',
                 'variation_details', 'quantity', 'price', 'total_price', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_product_image(self, obj):
        primary = obj.product.images.filter(is_primary=True).first()
        if primary and primary.image:
            return primary.image.url
        first_image = obj.product.images.first()
        return first_image.image.url if first_image and first_image.image else None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'subtotal',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ==================== Order Serializers ====================
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variation', 'product_name', 'sku',
                 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'payment_method', 'status', 'amount',
                 'transaction_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['id', 'status', 'message', 'location', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'subtotal', 'tax_amount',
                 'shipping_charge', 'discount_amount', 'total_amount',
                 'items_count', 'payment_status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.count()

    def get_payment_status(self, obj):
        payment = obj.payments.first()
        return payment.status if payment else 'pending'


class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(many=True, read_only=True)
    shipping_address_detail = AddressSerializer(source='shipping_address', read_only=True)
    billing_address_detail = AddressSerializer(source='billing_address', read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'items', 'payments', 'tracking', 'shipping_address',
            'shipping_address_detail', 'billing_address',
            'billing_address_detail', 'notes', 'cancellation_reason',
            'confirmed_at', 'shipped_at', 'delivered_at'
        ]


# ==================== Wishlist Serializers ====================
class WishlistSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_detail', 'created_at']
        read_only_fields = ['id', 'created_at']


# ==================== Recently Viewed Serializers ====================
class RecentlyViewedSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = RecentlyViewed
        fields = ['id', 'product', 'product_detail', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


# ==================== Review Serializers ====================
class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'product_name', 'user', 'user_name',
                 'rating', 'title', 'comment', 'is_verified_purchase',
                 'is_approved', 'helpful_count', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'is_verified_purchase', 'is_approved',
                           'helpful_count', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.mobile