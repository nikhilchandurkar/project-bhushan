
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, ProductImage, 
    ProductVariation, Order, OrderItem, 
    Review, User, Address, Cart, Payment,
    OTP, CartItem, OrderTracking, Wishlist,
    RecentlyViewed, ReviewImage,ContactMessage
)


# ============ INLINES (Reusable) ============
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'quantity', 'unit_price', 'total_price']
    can_delete = False


# ============ ADMIN CLASSES ============
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'display_order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'stock', 'is_active', 'image_tag']
    list_filter = ['is_active', 'is_featured', 'category', 'brand']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariationInline]
    
    def image_tag(self, obj):
        img = obj.images.filter(is_primary=True).first()
        return format_html('<img src="{}" width="50"/>', img.image.url) if img else "—"
    image_tag.short_description = 'Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'preview', 'is_primary']
    
    def preview(self, obj):
        return format_html('<img src="{}" width="75"/>', obj.image.url) if obj.image else "—"





@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__mobile']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase']
    actions = ['approve', 'reject']
    
    def approve(self, request, queryset):
        queryset.update(is_approved=True)
    
    def reject(self, request, queryset):
        queryset.update(is_approved=False)


# ============ SIMPLE REGISTRATIONS ============
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['mobile', 'email', 'is_mobile_verified', 'created_at']
    search_fields = ['mobile', 'email']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_type', 'city', 'is_default']
    list_filter = ['address_type', 'city']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'status', 'amount']
    list_filter = ['status', 'payment_method']




@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'phone', 'subject', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected messages as unread"
    
    actions = [mark_as_read, mark_as_unread]



class EcommerceAdminSite(admin.AdminSite):
    site_header = 'E-Commerce Admin'
    site_title = 'E-Commerce Admin Portal'
    index_title = 'Welcome to E-Commerce Administration'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Add statistics
        from django.db.models import Sum, Count
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        extra_context['total_users'] = User.objects.count()
        extra_context['total_products'] = Product.objects.filter(is_active=True).count()
        extra_context['total_orders'] = Order.objects.count()
        extra_context['orders_today'] = Order.objects.filter(created_at__date=today).count()
        extra_context['orders_this_week'] = Order.objects.filter(created_at__date__gte=week_ago).count()
        extra_context['revenue_today'] = Order.objects.filter(
            created_at__date=today, 
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        extra_context['revenue_this_month'] = Order.objects.filter(
            created_at__date__gte=month_ago,
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return super().index(request, extra_context)



#  Register remaining models with defaults
admin.site.register([OTP, ProductVariation, CartItem, OrderTracking, Wishlist, RecentlyViewed, ReviewImage])

