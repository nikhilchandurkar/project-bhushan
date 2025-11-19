import django_filters
from .models import Product, Order


class ProductFilter(django_filters.FilterSet):
    """Advanced product filtering"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    brand = django_filters.CharFilter(field_name='brand__slug')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    is_featured = django_filters.BooleanFilter()
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    
    class Meta:
        model = Product
        fields = ['name', 'min_price', 'max_price', 'category', 'brand',
                 'in_stock', 'is_featured', 'min_rating']
    
    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset
    
    def filter_min_rating(self, queryset, name, value):
        # Filter products with average rating >= value
        from django.db.models import Avg
        return queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=value)


class OrderFilter(django_filters.FilterSet):
    """Order filtering"""
    
    status = django_filters.CharFilter()
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    min_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    
    class Meta:
        model = Order
        fields = ['status', 'date_from', 'date_to', 'min_amount', 'max_amount']