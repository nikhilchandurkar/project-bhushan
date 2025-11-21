# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.html import format_html
# from django.db.models import Count, Sum, Avg
# from django.urls import reverse
# from django.utils.safestring import mark_safe
# from .models import (
#     User, OTP, Address, Category, Brand, Product, ProductImage,
#     ProductVariation, Cart, CartItem, Order, OrderItem, Payment,
#     OrderTracking, Wishlist, RecentlyViewed, Review, ReviewImage
# )


# # Inline Admin Classes
# class AddressInline(admin.TabularInline):
#     model = Address
#     extra = 0
#     fields = ('address_type', 'full_name', 'mobile', 'city', 'state', 'is_default')
#     readonly_fields = ('created_at',)


# class ProductImageInline(admin.TabularInline):
#     model = ProductImage
#     extra = 1
#     fields = ('image', 'alt_text', 'is_primary', 'display_order', 'image_preview')
#     readonly_fields = ('image_preview', 'created_at')

#     def image_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
#         return '-'
#     image_preview.short_description = 'Preview'


# class ProductVariationInline(admin.TabularInline):
#     model = ProductVariation
#     extra = 0
#     fields = ('variation_type', 'variation_value', 'price_adjustment', 'stock', 
#               'sku_suffix', 'is_active')


# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 0
#     readonly_fields = ('product', 'variation', 'quantity', 'price', 'total_price')
#     can_delete = False

#     def has_add_permission(self, request, obj=None):
#         return False


# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0
#     readonly_fields = ('product', 'product_name', 'sku', 'quantity', 
#                        'unit_price', 'total_price')
#     can_delete = False

#     def has_add_permission(self, request, obj=None):
#         return False


# class PaymentInline(admin.TabularInline):
#     model = Payment
#     extra = 0
#     readonly_fields = ('payment_method', 'status', 'amount', 'transaction_id', 'created_at')
#     can_delete = False

#     def has_add_permission(self, request, obj=None):
#         return False


# class OrderTrackingInline(admin.TabularInline):
#     model = OrderTracking
#     extra = 1
#     fields = ('status', 'message', 'location', 'created_at')
#     readonly_fields = ('created_at',)


# class ReviewImageInline(admin.TabularInline):
#     model = ReviewImage
#     extra = 0
#     fields = ('image', 'image_preview')
#     readonly_fields = ('image_preview',)

#     def image_preview(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" width="80" height="80" />', obj.image.url)
#         return '-'
#     image_preview.short_description = 'Preview'


# # Main Admin Classes
# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     list_display = ('mobile', 'username', 'email', 'full_name_display', 
#                     'is_mobile_verified', 'profile_completed', 'is_staff', 
#                     'created_at')
#     list_filter = ('is_staff', 'is_active', 'is_mobile_verified', 
#                    'profile_completed', 'gender', 'created_at')
#     search_fields = ('mobile', 'username', 'email', 'first_name', 'last_name')
#     ordering = ('-created_at',)
#     readonly_fields = ('id', 'created_at', 'updated_at', 'last_login', 'date_joined')
    
#     fieldsets = (
#         ('Authentication', {
#             'fields': ('id', 'mobile', 'username', 'password', 'is_mobile_verified')
#         }),
#         ('Personal Info', {
#             'fields': ('first_name', 'last_name', 'email', 'date_of_birth', 
#                       'gender', 'profile_completed')
#         }),
#         ('Permissions', {
#             'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 
#                       'user_permissions'),
#         }),
#         ('Important dates', {
#             'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
#         }),
#     )
    
#     inlines = [AddressInline]

#     def full_name_display(self, obj):
#         return obj.get_full_name() or '-'
#     full_name_display.short_description = 'Full Name'

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if not request.user.is_superuser:
#             return qs.filter(is_staff=False)
#         return qs


# @admin.register(OTP)
# class OTPAdmin(admin.ModelAdmin):
#     list_display = ('mobile', 'otp', 'is_verified', 'is_valid_display', 
#                     'created_at', 'expires_at')
#     list_filter = ('is_verified', 'created_at')
#     search_fields = ('mobile', 'otp')
#     readonly_fields = ('id', 'created_at')
#     ordering = ('-created_at',)

#     def is_valid_display(self, obj):
#         valid = obj.is_valid()
#         color = 'green' if valid else 'red'
#         return format_html('<span style="color: {};">{}</span>', 
#                           color, 'Valid' if valid else 'Invalid/Expired')
#     is_valid_display.short_description = 'Status'

#     def has_add_permission(self, request):
#         return False


# @admin.register(Address)
# class AddressAdmin(admin.ModelAdmin):
#     list_display = ('full_name', 'mobile', 'user_link', 'address_type', 
#                     'city', 'state', 'pincode', 'is_default')
#     list_filter = ('address_type', 'is_default', 'state', 'created_at')
#     search_fields = ('full_name', 'mobile', 'user__mobile', 'city', 
#                      'state', 'pincode')
#     readonly_fields = ('id', 'created_at', 'updated_at')
    
#     fieldsets = (
#         ('User', {
#             'fields': ('id', 'user', 'address_type', 'is_default')
#         }),
#         ('Contact Details', {
#             'fields': ('full_name', 'mobile')
#         }),
#         ('Address', {
#             'fields': ('address_line1', 'address_line2', 'landmark', 
#                       'city', 'state', 'pincode', 'country')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )

#     def user_link(self, obj):
#         url = reverse('admin:yourapp_user_change', args=[obj.user.id])
#         return format_html('<a href="{}">{}</a>', url, obj.user.mobile)
#     user_link.short_description = 'User'


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug', 'parent', 'is_active', 'product_count', 
#                     'display_order', 'created_at')
#     list_filter = ('is_active', 'parent', 'created_at')
#     search_fields = ('name', 'slug', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('id', 'created_at', 'updated_at', 'product_count')
#     ordering = ('display_order', 'name')
    
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('id', 'name', 'slug', 'parent', 'description')
#         }),
#         ('Media', {
#             'fields': ('image',)
#         }),
#         ('Settings', {
#             'fields': ('is_active', 'display_order', 'product_count')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )

#     def product_count(self, obj):
#         count = obj.products.count()
#         return format_html('<b>{}</b>', count)
#     product_count.short_description = 'Products'


# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug', 'is_active', 'product_count', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name', 'slug')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('id', 'created_at', 'product_count')

#     def product_count(self, obj):
#         count = obj.products.count()
#         return format_html('<b>{}</b>', count)
#     product_count.short_description = 'Products'


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'sku', 'category', 'brand', 'price_display', 
#                     'stock_status', 'sales_count', 'rating_display', 
#                     'is_active', 'is_featured', 'created_at')
#     list_filter = ('is_active', 'is_featured', 'category', 'brand', 'created_at')
#     search_fields = ('name', 'sku', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('id', 'views_count', 'sales_count', 'rating_display', 
#                        'discount_percentage', 'created_at', 'updated_at')
#     ordering = ('-created_at',)
    
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('id', 'name', 'slug', 'sku', 'category', 'brand')
#         }),
#         ('Description', {
#             'fields': ('short_description', 'description')
#         }),
#         ('Pricing', {
#             'fields': ('price', 'compare_price', 'cost_price', 'discount_percentage')
#         }),
#         ('Inventory', {
#             'fields': ('stock', 'low_stock_threshold')
#         }),
#         ('Settings', {
#             'fields': ('is_active', 'is_featured')
#         }),
#         ('Statistics', {
#             'fields': ('views_count', 'sales_count', 'rating_display')
#         }),
#         ('SEO', {
#             'fields': ('meta_title', 'meta_description'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )
    
#     inlines = [ProductImageInline, ProductVariationInline]

#     def price_display(self, obj):
#         if obj.compare_price and obj.compare_price > obj.price:
#             return format_html(
#                 '₹{} <s style="color: red;">₹{}</s> <span style="color: green;">{}% off</span>',
#                 obj.price, obj.compare_price, obj.discount_percentage
#             )
#         return f'₹{obj.price}'
#     price_display.short_description = 'Price'

#     def stock_status(self, obj):
#         if obj.stock == 0:
#             color = 'red'
#             status = 'Out of Stock'
#         elif obj.is_low_stock:
#             color = 'orange'
#             status = f'Low Stock ({obj.stock})'
#         else:
#             color = 'green'
#             status = f'In Stock ({obj.stock})'
#         return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
#                           color, status)
#     stock_status.short_description = 'Stock'

#     def rating_display(self, obj):
#         rating = obj.average_rating
#         if rating:
#             stars = '★' * int(rating) + '☆' * (5 - int(rating))
#             return format_html('{} ({:.1f}/5)', stars, rating)
#         return 'No ratings'
#     rating_display.short_description = 'Rating'


# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'total_items', 'subtotal_display', 'updated_at')
#     search_fields = ('user__mobile', 'user__email')
#     readonly_fields = ('id', 'created_at', 'updated_at', 'total_items', 'subtotal_display')
#     inlines = [CartItemInline]

#     def subtotal_display(self, obj):
#         return f'₹{obj.subtotal}'
#     subtotal_display.short_description = 'Subtotal'


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('order_number', 'user_link', 'status_badge', 'total_amount_display', 
#                     'payment_status', 'items_count', 'created_at')
#     list_filter = ('status', 'created_at', 'confirmed_at', 'shipped_at', 'delivered_at')
#     search_fields = ('order_number', 'user__mobile', 'user__email', 
#                      'shipping_address__mobile')
#     readonly_fields = ('id', 'order_number', 'created_at', 'updated_at', 
#                        'confirmed_at', 'shipped_at', 'delivered_at', 'items_count')
#     ordering = ('-created_at',)
#     date_hierarchy = 'created_at'
    
#     fieldsets = (
#         ('Order Info', {
#             'fields': ('id', 'order_number', 'user', 'status', 'items_count')
#         }),
#         ('Addresses', {
#             'fields': ('shipping_address', 'billing_address')
#         }),
#         ('Pricing', {
#             'fields': ('subtotal', 'tax_amount', 'shipping_charge', 
#                       'discount_amount', 'total_amount')
#         }),
#         ('Additional Info', {
#             'fields': ('notes', 'cancellation_reason')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'confirmed_at', 
#                       'shipped_at', 'delivered_at')
#         }),
#     )
    
#     inlines = [OrderItemInline, PaymentInline, OrderTrackingInline]

#     def user_link(self, obj):
#         url = reverse('admin:yourapp_user_change', args=[obj.user.id])
#         return format_html('<a href="{}">{}</a>', url, obj.user.mobile)
#     user_link.short_description = 'User'

#     def status_badge(self, obj):
#         colors = {
#             'pending': 'orange',
#             'confirmed': 'blue',
#             'processing': 'purple',
#             'shipped': 'cyan',
#             'delivered': 'green',
#             'cancelled': 'red',
#             'refunded': 'gray'
#         }
#         color = colors.get(obj.status, 'black')
#         return format_html(
#             '<span style="background-color: {}; color: white; padding: 3px 10px; '
#             'border-radius: 3px; font-weight: bold;">{}</span>',
#             color, obj.get_status_display()
#         )
#     status_badge.short_description = 'Status'

#     def total_amount_display(self, obj):
#         return format_html('<b>₹{}</b>', obj.total_amount)
#     total_amount_display.short_description = 'Total'

#     def payment_status(self, obj):
#         payment = obj.payments.first()
#         if payment:
#             colors = {
#                 'pending': 'orange',
#                 'processing': 'blue',
#                 'completed': 'green',
#                 'failed': 'red',
#                 'refunded': 'gray'
#             }
#             color = colors.get(payment.status, 'black')
#             return format_html(
#                 '<span style="color: {}; font-weight: bold;">{}</span>',
#                 color, payment.get_status_display()
#             )
#         return '-'
#     payment_status.short_description = 'Payment'

#     def items_count(self, obj):
#         count = obj.items.count()
#         return format_html('<b>{}</b>', count)
#     items_count.short_description = 'Items'


# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('order_link', 'payment_method', 'status_badge', 
#                     'amount_display', 'transaction_id', 'created_at')
#     list_filter = ('payment_method', 'status', 'created_at')
#     search_fields = ('order__order_number', 'transaction_id')
#     readonly_fields = ('id', 'created_at', 'updated_at', 'gateway_response')
#     ordering = ('-created_at',)

#     def order_link(self, obj):
#         url = reverse('admin:yourapp_order_change', args=[obj.order.id])
#         return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
#     order_link.short_description = 'Order'

#     def status_badge(self, obj):
#         colors = {
#             'pending': 'orange',
#             'processing': 'blue',
#             'completed': 'green',
#             'failed': 'red',
#             'refunded': 'gray'
#         }
#         color = colors.get(obj.status, 'black')
#         return format_html(
#             '<span style="background-color: {}; color: white; padding: 3px 10px; '
#             'border-radius: 3px;">{}</span>',
#             color, obj.get_status_display()
#         )
#     status_badge.short_description = 'Status'

#     def amount_display(self, obj):
#         return format_html('<b>₹{}</b>', obj.amount)
#     amount_display.short_description = 'Amount'


# @admin.register(Wishlist)
# class WishlistAdmin(admin.ModelAdmin):
#     list_display = ('user', 'product', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('user__mobile', 'product__name')
#     readonly_fields = ('id', 'created_at')


# @admin.register(RecentlyViewed)
# class RecentlyViewedAdmin(admin.ModelAdmin):
#     list_display = ('user', 'product', 'viewed_at')
#     list_filter = ('viewed_at',)
#     search_fields = ('user__mobile', 'product__name')
#     readonly_fields = ('id', 'viewed_at')
#     ordering = ('-viewed_at',)


# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('user', 'product', 'rating_stars', 'title', 
#                     'is_verified_purchase', 'is_approved', 'helpful_count', 
#                     'created_at')
#     list_filter = ('rating', 'is_verified_purchase', 'is_approved', 'created_at')
#     search_fields = ('user__mobile', 'product__name', 'title', 'comment')
#     readonly_fields = ('id', 'helpful_count', 'created_at', 'updated_at')
#     ordering = ('-created_at',)
    
#     fieldsets = (
#         ('Review Info', {
#             'fields': ('id', 'product', 'user', 'order_item')
#         }),
#         ('Rating & Content', {
#             'fields': ('rating', 'title', 'comment')
#         }),
#         ('Status', {
#             'fields': ('is_verified_purchase', 'is_approved', 'helpful_count')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )
    
#     inlines = [ReviewImageInline]
#     actions = ['approve_reviews', 'disapprove_reviews']

#     def rating_stars(self, obj):
#         stars = '★' * obj.rating + '☆' * (5 - obj.rating)
#         return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
#     rating_stars.short_description = 'Rating'

#     def approve_reviews(self, request, queryset):
#         count = queryset.update(is_approved=True)
#         self.message_user(request, f'{count} review(s) approved.')
#     approve_reviews.short_description = 'Approve selected reviews'

#     def disapprove_reviews(self, request, queryset):
#         count = queryset.update(is_approved=False)
#         self.message_user(request, f'{count} review(s) disapproved.')
#     disapprove_reviews.short_description = 'Disapprove selected reviews'


# # Dashboard Statistics (optional - for custom admin dashboard)


# # Uncomment below to use custom admin site
# admin_site = EcommerceAdminSite(name='ecommerce_admin-bhushan-website')





























"""
shop/admin.py - Condensed version with SAME functionality
Uses Django's defaults intelligently to reduce code
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import *


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

