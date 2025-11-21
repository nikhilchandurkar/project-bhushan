# cache_utils.py
# Place this file in your Django app directory for easy cache management

from django.core.cache import cache
from django.db.models import Count, Q, F
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Cache Configuration
# ==========================================

CACHE_TIMEOUT = 3600  # 1 hour
NEW_PRODUCT_DAYS = 7  # Products created within last 7 days
CACHE_VERSION = 1  # Increment this to invalidate all caches

# ==========================================
# Cache Keys Manager
# ==========================================

class CacheKeys:
    """Centralized cache keys management"""
    
    # Product caches
    ALL_PRODUCTS = 'products:all'
    FEATURED_PRODUCTS = 'products:featured:home'
    NEW_ARRIVALS = 'products:new:home'
    TOP_SELLING = 'products:top_selling:home'
    PRICE_RANGE = 'products:price_range'
    
    # Category caches
    ACTIVE_CATEGORIES = 'categories:active'
    MEGA_MENU_CATEGORIES = 'categories:mega_menu'
    
    # Brand caches
    ACTIVE_BRANDS = 'brands:active'
    
    # Filtered products (pattern)
    FILTERED_PRODUCTS_PATTERN = 'products:filtered:*'
    
    @staticmethod
    def filtered_products_key(category=None, brand=None, tab='all', search='', 
                            min_price=0, max_price=999999, sort='-is_featured'):
        """Generate cache key for filtered products"""
        params = f"{category}_{brand}_{tab}_{search}_{min_price}_{max_price}_{sort}"
        hash_val = hashlib.md5(params.encode()).hexdigest()
        return f'products:filtered:{hash_val}'


# ==========================================
# Cache Manager Class
# ==========================================

class CacheManager:
    """
    Centralized cache management for the application.
    Handles setting, getting, and clearing caches with proper logging.
    """
    
    @staticmethod
    def get(key, default=None):
        """Get value from cache"""
        try:
            value = cache.get(key)
            if value is not None:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value if value is not None else default
        except Exception as e:
            logger.error(f"Error getting cache {key}: {str(e)}")
            return default
    
    @staticmethod
    def set(key, value, timeout=CACHE_TIMEOUT):
        """Set value in cache"""
        try:
            cache.set(key, value, timeout)
            logger.debug(f"Cache SET: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache {key}: {str(e)}")
            return False
    
    @staticmethod
    def delete(key):
        """Delete value from cache"""
        try:
            cache.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {str(e)}")
            return False
    
    @staticmethod
    def delete_many(keys):
        """Delete multiple cache keys"""
        try:
            cache.delete_many(keys)
            logger.debug(f"Cache DELETE MANY: {len(keys)} keys")
            return True
        except Exception as e:
            logger.error(f"Error deleting cache keys: {str(e)}")
            return False
    
    @staticmethod
    def get_or_set(key, default_func, timeout=CACHE_TIMEOUT):
        """Get from cache or set if not exists"""
        value = CacheManager.get(key)
        if value is None:
            try:
                value = default_func()
                CacheManager.set(key, value, timeout)
            except Exception as e:
                logger.error(f"Error in get_or_set for {key}: {str(e)}")
                value = None
        return value
    
    @staticmethod
    def clear_pattern(pattern):
        """Clear all cache keys matching a pattern"""
        try:
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)
                logger.info(f"Cache pattern DELETE: {pattern} ({len(keys)} keys)")
            return len(keys)
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0


# ==========================================
# Product Cache Functions
# ==========================================

def get_all_products_cached(query_func=None):
    """
    Get all products from cache or fetch if not cached.
    query_func should be a callable that returns the products queryset.
    """
    def fetch_products():
        if query_func:
            return list(query_func())
        from .models import Product, ProductImage
        from django.db.models import Prefetch, Case, When, Value, DecimalField, F
        from django.utils import timezone
        from datetime import timedelta
        
        new_date = timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)
        primary_image_qs = ProductImage.objects.filter(is_primary=True)
        
        return list(
            Product.objects.filter(is_active=True).select_related(
                "category", "brand"
            ).prefetch_related(
                Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
            ).annotate(
                is_new=Case(
                    When(created_at__gte=new_date, then=Value(True)),
                    default=Value(False)
                )
            ).values(
                'id', 'name', 'slug', 'price', 'compare_price',
                'is_featured', 'stock', 'sales_count', 'category__name', 'brand__name'
            )[:1000]
        )
    
    return CacheManager.get_or_set(CacheKeys.ALL_PRODUCTS, fetch_products)


def get_featured_products_cached(limit=8):
    """Get featured products from cache"""
    def fetch_featured():
        from .models import Product, ProductImage
        from django.db.models import Prefetch
        
        primary_image_qs = ProductImage.objects.filter(is_primary=True)
        return list(
            Product.objects.filter(is_active=True, is_featured=True)
            .select_related("category", "brand")
            .prefetch_related(
                Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
            ).order_by('-created_at')[:limit]
        )
    
    return CacheManager.get_or_set(CacheKeys.FEATURED_PRODUCTS, fetch_featured)


def get_new_arrivals_cached(limit=8):
    """Get new arrival products from cache"""
    def fetch_new():
        from .models import Product, ProductImage
        from django.db.models import Prefetch
        from django.utils import timezone
        from datetime import timedelta
        
        new_date = timezone.now() - timedelta(days=NEW_PRODUCT_DAYS)
        primary_image_qs = ProductImage.objects.filter(is_primary=True)
        
        return list(
            Product.objects.filter(is_active=True, created_at__gte=new_date)
            .select_related("category", "brand")
            .prefetch_related(
                Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
            ).order_by('-created_at')[:limit]
        )
    
    return CacheManager.get_or_set(CacheKeys.NEW_ARRIVALS, fetch_new)


def get_top_selling_products_cached(limit=8):
    """Get top selling products from cache"""
    def fetch_top():
        from .models import Product, ProductImage
        from django.db.models import Prefetch
        
        primary_image_qs = ProductImage.objects.filter(is_primary=True)
        return list(
            Product.objects.filter(is_active=True, sales_count__gt=0)
            .select_related("category", "brand")
            .prefetch_related(
                Prefetch("images", queryset=primary_image_qs, to_attr="primary_images")
            ).order_by('-sales_count', '-created_at')[:limit]
        )
    
    return CacheManager.get_or_set(CacheKeys.TOP_SELLING, fetch_top)


def get_price_range_cached():
    """Get product price range from cache"""
    def fetch_price_range():
        from .models import Product
        from django.db.models import Min, Max, Case, When, F
        
        price_stats = Product.objects.filter(
            is_active=True
        ).aggregate(
            min_price=Min(Case(
                When(compare_price__gt=0, then='compare_price'),
                default='price'
            )),
            max_price=Max('price')
        )
        
        return {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 0)
        }
    
    return CacheManager.get_or_set(CacheKeys.PRICE_RANGE, fetch_price_range)


# ==========================================
# Category Cache Functions
# ==========================================

def get_active_categories_cached():
    """Get active categories from cache"""
    def fetch_categories():
        from .models import Category
        
        return list(
            Category.objects.filter(
                is_active=True, parent=None
            ).prefetch_related('children').values(
                'id', 'name', 'slug'
            )
        )
    
    return CacheManager.get_or_set(CacheKeys.ACTIVE_CATEGORIES, fetch_categories)


def get_mega_menu_categories_cached():
    """Get mega menu categories from cache"""
    def fetch_mega_menu():
        from .models import Category
        
        return list(
            Category.objects.filter(is_active=True, parent=None)
            .prefetch_related('children')[:4]
        )
    
    return CacheManager.get_or_set(CacheKeys.MEGA_MENU_CATEGORIES, fetch_mega_menu)


# ==========================================
# Brand Cache Functions
# ==========================================

def get_active_brands_cached():
    """Get active brands from cache"""
    def fetch_brands():
        from .models import Brand
        
        return list(
            Brand.objects.filter(
                is_active=True
            ).annotate(
                product_count=Count('products', filter=Q(products__is_active=True))
            ).filter(
                product_count__gt=0
            ).values('id', 'name', 'slug', 'product_count').order_by('name')
        )
    
    return CacheManager.get_or_set(CacheKeys.ACTIVE_BRANDS, fetch_brands)


# ==========================================
# Cache Statistics and Monitoring
# ==========================================

def get_cache_statistics():
    """Get statistics about all cached items"""
    return {
        'all_products': CacheManager.get(CacheKeys.ALL_PRODUCTS) is not None,
        'featured_products': CacheManager.get(CacheKeys.FEATURED_PRODUCTS) is not None,
        'new_arrivals': CacheManager.get(CacheKeys.NEW_ARRIVALS) is not None,
        'top_selling': CacheManager.get(CacheKeys.TOP_SELLING) is not None,
        'price_range': CacheManager.get(CacheKeys.PRICE_RANGE) is not None,
        'active_categories': CacheManager.get(CacheKeys.ACTIVE_CATEGORIES) is not None,
        'mega_menu_categories': CacheManager.get(CacheKeys.MEGA_MENU_CATEGORIES) is not None,
        'active_brands': CacheManager.get(CacheKeys.ACTIVE_BRANDS) is not None,
    }


def clear_all_product_caches():
    """Clear all product-related caches"""
    keys_to_delete = [
        CacheKeys.ALL_PRODUCTS,
        CacheKeys.FEATURED_PRODUCTS,
        CacheKeys.NEW_ARRIVALS,
        CacheKeys.TOP_SELLING,
        CacheKeys.PRICE_RANGE,
    ]
    
    for key in keys_to_delete:
        CacheManager.delete(key)
    
    # Clear filtered products pattern
    CacheManager.clear_pattern(CacheKeys.FILTERED_PRODUCTS_PATTERN)
    
    logger.info("All product caches cleared")


def clear_all_caches():
    """Clear all application caches"""
    clear_all_product_caches()
    CacheManager.delete(CacheKeys.ACTIVE_CATEGORIES)
    CacheManager.delete(CacheKeys.MEGA_MENU_CATEGORIES)
    CacheManager.delete(CacheKeys.ACTIVE_BRANDS)
    logger.info("All caches cleared")