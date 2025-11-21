# signals.py
from django.dispatch import receiver
from .models import OrderItem, Product,Product, Category, Brand,ProductImage

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db.models import Q
import logging


logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderItem)
def update_inventory(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.stock -= instance.quantity
        product.sales_count += instance.quantity
        product.save()
        
        if instance.variation:
            instance.variation.stock -= instance.quantity
            instance.variation.save()




@receiver(post_save, sender=Product)
def invalidate_product_cache_on_save(sender, instance=None, created=False, **kwargs):
    """Invalidate caches when product is saved"""
    invalidate_product_cache()
    if created:
        invalidate_category_cache()


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance=None, **kwargs):
    """Invalidate caches when product is deleted"""
    invalidate_product_cache()


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache_signals(sender, **kwargs):
    """Invalidate category caches"""
    invalidate_category_cache()


@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
def invalidate_brand_cache_signals(sender, **kwargs):
    """Invalidate brand caches"""
    invalidate_brand_cache()


def invalidate_product_cache():
    """Clear all product-related caches"""
    cache.delete('all_products')
    cache.delete('featured_products_home')
    cache.delete('new_arrivals_home')
    cache.delete('top_selling_home')
    cache.delete('product_price_range')
    
    # Clear all filter caches
    keys = cache.keys('filtered_products_*')
    if keys:
        cache.delete_many(keys)


def invalidate_category_cache():
    """Clear category caches"""
    cache.delete('active_categories')
    cache.delete('categories_mega_menu')
    invalidate_product_cache()


def invalidate_brand_cache():
    """Clear brand caches"""
    cache.delete('active_brands')
    invalidate_product_cache()




CACHE_KEYS = {
    'all_products': 'all_products',
    'featured_products_home': 'featured_products_home',
    'new_arrivals_home': 'new_arrivals_home',
    'top_selling_home': 'top_selling_home',
    'product_price_range': 'product_price_range',
    'active_categories': 'active_categories',
    'categories_mega_menu': 'categories_mega_menu',
    'active_brands': 'active_brands',
    'filtered_products': 'filtered_products_*',
}

# ==========================================
# Product Signals
# ==========================================

@receiver(post_save, sender=Product)
def invalidate_product_cache_on_save(sender, instance=None, created=False, **kwargs):
    """
    Invalidate product-related caches when a product is saved.
    This includes both new product creation and product updates.
    """
    try:
        logger.info(f"Product saved: {instance.name} (ID: {instance.id})")
        
        # Invalidate all product caches
        invalidate_all_product_caches()
        
        # If product is new and active, also invalidate category cache
        if created and instance.is_active:
            invalidate_category_cache()
            
            logger.info(f"New active product created: {instance.name}")
        
        # If product featured status changed, invalidate featured products cache
        if instance.is_featured:
            cache.delete(CACHE_KEYS['featured_products_home'])
            logger.info(f"Featured status changed for: {instance.name}")
            
    except Exception as e:
        logger.error(f"Error invalidating product cache on save: {str(e)}")


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance=None, **kwargs):
    """
    Invalidate product-related caches when a product is deleted.
    """
    try:
        logger.info(f"Product deleted: {instance.name} (ID: {instance.id})")
        invalidate_all_product_caches()
        
        # Also invalidate category cache
        invalidate_category_cache()
        
    except Exception as e:
        logger.error(f"Error invalidating product cache on delete: {str(e)}")


# ==========================================
# ProductImage Signals
# ==========================================

@receiver(post_save, sender=ProductImage)
def invalidate_cache_on_image_save(sender, instance=None, created=False, **kwargs):
    """
    Invalidate product cache when product images are updated.
    This ensures the product display is updated with new images.
    """
    try:
        if instance and instance.product:
            logger.info(f"Product image saved for: {instance.product.name}")
            invalidate_all_product_caches()
            
    except Exception as e:
        logger.error(f"Error invalidating cache on image save: {str(e)}")


@receiver(post_delete, sender=ProductImage)
def invalidate_cache_on_image_delete(sender, instance=None, **kwargs):
    """
    Invalidate product cache when product images are deleted.
    """
    try:
        if instance and instance.product:
            logger.info(f"Product image deleted for: {instance.product.name}")
            invalidate_all_product_caches()
            
    except Exception as e:
        logger.error(f"Error invalidating cache on image delete: {str(e)}")


# ==========================================
# Category Signals
# ==========================================

@receiver(post_save, sender=Category)
def invalidate_category_cache_on_save(sender, instance=None, created=False, **kwargs):
    """
    Invalidate category-related caches when a category is saved.
    """
    try:
        logger.info(f"Category saved: {instance.name} (ID: {instance.id})")
        invalidate_category_cache()
        
        # Also invalidate product caches since categories affect product listings
        invalidate_all_product_caches()
        
    except Exception as e:
        logger.error(f"Error invalidating category cache on save: {str(e)}")


@receiver(post_delete, sender=Category)
def invalidate_category_cache_on_delete(sender, instance=None, **kwargs):
    """
    Invalidate category-related caches when a category is deleted.
    """
    try:
        logger.info(f"Category deleted: {instance.name} (ID: {instance.id})")
        invalidate_category_cache()
        invalidate_all_product_caches()
        
    except Exception as e:
        logger.error(f"Error invalidating category cache on delete: {str(e)}")


# ==========================================
# Brand Signals
# ==========================================

@receiver(post_save, sender=Brand)
def invalidate_brand_cache_on_save(sender, instance=None, created=False, **kwargs):
    """
    Invalidate brand-related caches when a brand is saved.
    """
    try:
        logger.info(f"Brand saved: {instance.name} (ID: {instance.id})")
        invalidate_brand_cache()
        
        # Also invalidate product caches
        invalidate_all_product_caches()
        
    except Exception as e:
        logger.error(f"Error invalidating brand cache on save: {str(e)}")


@receiver(post_delete, sender=Brand)
def invalidate_brand_cache_on_delete(sender, instance=None, **kwargs):
    """
    Invalidate brand-related caches when a brand is deleted.
    """
    try:
        logger.info(f"Brand deleted: {instance.name} (ID: {instance.id})")
        invalidate_brand_cache()
        invalidate_all_product_caches()
        
    except Exception as e:
        logger.error(f"Error invalidating brand cache on delete: {str(e)}")


# ==========================================
# Cache Invalidation Helper Functions
# ==========================================

def invalidate_all_product_caches():
    """
    Clear all product-related cache keys.
    This includes home page product caches and filtered product caches.
    """
    cache_keys_to_delete = [
        CACHE_KEYS['all_products'],
        CACHE_KEYS['featured_products_home'],
        CACHE_KEYS['new_arrivals_home'],
        CACHE_KEYS['top_selling_home'],
        CACHE_KEYS['product_price_range'],
    ]
    
    for key in cache_keys_to_delete:
        try:
            cache.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {str(e)}")
    
    # Clear all filtered products cache (pattern-based deletion)
    try:
        filtered_keys = cache.keys(CACHE_KEYS['filtered_products'])
        if filtered_keys:
            cache.delete_many(filtered_keys)
            logger.debug(f"Deleted {len(filtered_keys)} filtered product cache entries")
    except Exception as e:
        logger.warning(f"Failed to delete filtered products cache: {str(e)}")


def invalidate_category_cache():
    """
    Clear all category-related cache keys.
    """
    cache_keys_to_delete = [
        CACHE_KEYS['active_categories'],
        CACHE_KEYS['categories_mega_menu'],
    ]
    
    for key in cache_keys_to_delete:
        try:
            cache.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {str(e)}")


def invalidate_brand_cache():
    """
    Clear all brand-related cache keys.
    """
    try:
        cache.delete(CACHE_KEYS['active_brands'])
        logger.debug(f"Cache deleted: {CACHE_KEYS['active_brands']}")
    except Exception as e:
        logger.warning(f"Failed to delete cache key {CACHE_KEYS['active_brands']}: {str(e)}")


def clear_all_caches():
    """
    Clear all application caches.
    Use this for bulk operations or manual cache clearing.
    """
    try:
        invalidate_all_product_caches()
        invalidate_category_cache()
        invalidate_brand_cache()
        logger.info("All caches cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing all caches: {str(e)}")


# ==========================================
# Optional: Bulk Operation Cache Clearing
# ==========================================

def invalidate_product_by_category(category_id):
    """
    Invalidate caches for a specific category's products.
    Useful if you have category-specific product caches.
    """
    try:
        # Check if any products belong to this category
        product_count = Product.objects.filter(category_id=category_id).count()
        if product_count > 0:
            invalidate_all_product_caches()
            logger.info(f"Invalidated cache for {product_count} products in category {category_id}")
    except Exception as e:
        logger.error(f"Error invalidating products by category: {str(e)}")


def invalidate_product_by_brand(brand_id):
    """
    Invalidate caches for a specific brand's products.
    """
    try:
        product_count = Product.objects.filter(brand_id=brand_id).count()
        if product_count > 0:
            invalidate_all_product_caches()
            logger.info(f"Invalidated cache for {product_count} products in brand {brand_id}")
    except Exception as e:
        logger.error(f"Error invalidating products by brand: {str(e)}")


# ==========================================
# Management Command Helper
# ==========================================

def get_cache_statistics():
    """
    Get statistics about cached items.
    Useful for monitoring cache performance.
    """
    try:
        stats = {
            'all_products': cache.get(CACHE_KEYS['all_products']) is not None,
            'featured_products_home': cache.get(CACHE_KEYS['featured_products_home']) is not None,
            'new_arrivals_home': cache.get(CACHE_KEYS['new_arrivals_home']) is not None,
            'top_selling_home': cache.get(CACHE_KEYS['top_selling_home']) is not None,
            'product_price_range': cache.get(CACHE_KEYS['product_price_range']) is not None,
            'active_categories': cache.get(CACHE_KEYS['active_categories']) is not None,
            'categories_mega_menu': cache.get(CACHE_KEYS['categories_mega_menu']) is not None,
            'active_brands': cache.get(CACHE_KEYS['active_brands']) is not None,
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting cache statistics: {str(e)}")
        return {}