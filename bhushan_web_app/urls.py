from django.urls import path
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    
HomeView,ProductsView,AuthPageView,SendOTPView,VerifyOTPView,LogoutView,CategoryProductsView,
)
app_name = 'shop'
# API Router for ViewSets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')

urlpatterns = [
   path("", HomeView.as_view(), name="home"),
   
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions_view, name='terms_conditions'),
    path('return-policy/', views.return_policy_view, name='return_policy'),

   path('products/', views.ProductsView.as_view(), name='products'),
   path('api/products/filtered/', views.get_filtered_products, name='api_filtered_products'),
    # Authentication URLs
    path("auth/", AuthPageView.as_view(), name="auth-page"),
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('auth/profile/complete/', views.CompleteProfileView.as_view(), name='complete-profile'),
    
    # Address URLs
    path('addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<uuid:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<uuid:pk>/set-default/', views.SetDefaultAddressView.as_view(), name='set-default-address'),
    
    # Product URLs
    path('products/featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('products/trending/', views.TrendingProductsView.as_view(), name='trending-products'),
    path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<uuid:pk>/track-view/', views.TrackProductViewView.as_view(), name='track-view'),
    
    # Category URLs
    # path('categories/tree/', views.CategoryTreeView.as_view(), name='category-tree'),
  
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='category_products'),
    
    # Cart URLs
    path('cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart/add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('cart/update/<uuid:pk>/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/remove/<uuid:pk>/', views.RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear-cart'),
    
    # Wishlist URLs
    path('wishlist/', views.WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/add/', views.AddToWishlistView.as_view(), name='add-to-wishlist'),
    path('wishlist/remove/<uuid:pk>/', views.RemoveFromWishlistView.as_view(), name='remove-from-wishlist'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<uuid:pk>/tracking/', views.OrderTrackingView.as_view(), name='order-tracking'),
    
    # Payment URLs
    path('payments/initiate/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/', views.VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
    
    # Review URLs
    path('reviews/product/<uuid:product_id>/', views.ProductReviewsView.as_view(), name='product-reviews'),
    path('reviews/create/', views.CreateReviewView.as_view(), name='create-review'),
    path('reviews/<uuid:pk>/helpful/', views.MarkReviewHelpfulView.as_view(), name='mark-review-helpful'),
    
    # User Activity URLs
    path('recently-viewed/', views.RecentlyViewedView.as_view(), name='recently-viewed'),
    path('dashboard/', views.UserDashboardView.as_view(), name='user-dashboard'),
    
    # Brand URLs
    path('brands/', views.BrandListView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/products/', views.BrandProductsView.as_view(), name='brand-products'),
    
    # API Router URLs
    path('api/', include(router.urls)),
]


