"""
Create this file: shop/context_processors.py

"""

from .models import Cart, Category

def cart_context(request):
    """Add cart count to all templates"""
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.total_items
        except Cart.DoesNotExist:
            cart_count = 0
    
    return {
        'cart_count': cart_count
    }


def categories_context(request):
    """Add categories to all templates for mega menu"""
    categories = Category.objects.filter(
        is_active=True, 
        parent=None
    ).prefetch_related('children')[:8]
    
    return {
        'categories': categories
    }


# Then add to settings.py TEMPLATES context_processors:
"""
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... existing processors
                'shop.context_processors.cart_context',
                'shop.context_processors.categories_context',
            ],
        },
    },
]
"""