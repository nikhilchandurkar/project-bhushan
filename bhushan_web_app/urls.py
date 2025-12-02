from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    # Home & Pages
    HomeView, ProductsView,
    
    # Auth
    AuthPageView, SendOTPView, VerifyOTPView, LogoutView,
    
    # Products & Categories
    CategoryProductsView, ProductDetailView, get_filtered_products,
    
    # Cart & Profile Pages (NEW VIEWS)
    CartPageView,
    UserProfilePageView,
    ProfileCompletionPageView,
    AddressCreateView,
    AddressUpdateView,
    AddressDetailAPIView,
)

app_name = 'shop'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')

urlpatterns = [
    # ==================== Home & Static Pages ====================
    path("", HomeView.as_view(), name="home"),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy-policy'),
    path('terms-conditions/', views.terms_conditions_view, name='terms-conditions'),
    path('return-policy/', views.return_policy_view, name='return-policy'),

    # ==================== Product Pages ====================
    path('products/', ProductsView.as_view(), name='products'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('products/trending/', views.TrendingProductsView.as_view(), name='trending-products'),
    path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    path('products/<uuid:pk>/track-view/', views.TrackProductViewView.as_view(), name='track-view'),
    path('api/products/filtered/', get_filtered_products, name='api-filtered-products'),

    # ==================== Category Pages ====================
    path('categories/tree/', views.CategoryTreeView.as_view(), name='category-tree'),
    path('category/<slug:slug>/products/', CategoryProductsView.as_view(), name='category-products'),

    # ==================== Authentication ====================
    path("auth/", AuthPageView.as_view(), name="auth-page"),
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    
    # ==================== Profile Pages (TEMPLATE VIEWS - NEW) ====================
    path("profile/", UserProfilePageView.as_view(), name="user-profile"),
    path("profile/complete/", ProfileCompletionPageView.as_view(), name="profile-completion"),
    
    # Profile API Endpoints (for AJAX/API requests)
    path("auth/profile/", views.UserProfileView.as_view(), name="api-user-profile"),
    path("auth/profile/complete/", views.CompleteProfileView.as_view(), name="complete-profile"),

    # ==================== Address Management (NEW) ====================
    # Template-based address management
    path('addresses/add/', AddressCreateView.as_view(), name='address-create'),
    path('addresses/<uuid:pk>/edit/', AddressUpdateView.as_view(), name='address-edit'),
    
    # API endpoints for addresses
    path('addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<uuid:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<uuid:pk>/set-default/', views.SetDefaultAddressView.as_view(), name='set-default-address'),
    path('api/addresses/<uuid:pk>/', AddressDetailAPIView.as_view(), name='api-address-detail'),

    # ==================== Cart (NEW) ====================
    # Template view for cart page
    path('cart/', CartPageView.as_view(), name='cart-page'),
    
    # API endpoints for cart operations
    path('cart/api/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/items/<uuid:pk>/update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/items/<uuid:pk>/remove/', views.RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear-cart'),

    # ==================== Wishlist ====================
    path('wishlist/', views.WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/add/', views.AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('wishlist/remove/<uuid:pk>/', views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),

    # ==================== Orders ====================
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<uuid:pk>/tracking/', views.OrderTrackingView.as_view(), name='order-tracking'),

    # ==================== Payments ====================
    path('payments/initiate/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/', views.VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),

    # ==================== Reviews ====================
    path('reviews/product/<uuid:product_id>/', views.ProductReviewsView.as_view(), name='product-reviews'),
    path('reviews/create/', views.CreateReviewView.as_view(), name='create-review'),
    path('reviews/<uuid:pk>/helpful/', views.MarkReviewHelpfulView.as_view(), name='mark-review-helpful'),

    # ==================== User Dashboard & Activity ====================
    path('recently-viewed/', views.RecentlyViewedView.as_view(), name='recently-viewed'),
    path('dashboard/', views.UserDashboardView.as_view(), name='user-dashboard'),

    # ==================== Brands ====================
    path('brands/', views.BrandListView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/products/', views.BrandProductsView.as_view(), name='brand-products'),

    # ==================== API Router ====================
    path('api/', include(router.urls)),
]