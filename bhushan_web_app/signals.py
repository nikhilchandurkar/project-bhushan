# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrderItem, Product

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