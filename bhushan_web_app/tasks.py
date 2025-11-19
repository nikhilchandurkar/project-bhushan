from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

# ==================== SMS Tasks ====================
@shared_task(bind=True, max_retries=3)
def send_sms_otp(self, mobile, otp):
    """Send OTP via Twilio SMS"""
    try:
        from twilio.rest import Client
        
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        message = client.messages.create(
            body=f'Your OTP is: {otp}. Valid for 10 minutes.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=mobile
        )
        
        logger.info(f'SMS sent to {mobile}: {message.sid}')
        return {'status': 'success', 'sid': message.sid}
        
    except Exception as e:
        logger.error(f'SMS failed for {mobile}: {e}')
        raise self.retry(exc=e, countdown=60)


# ==================== Email Tasks ====================
@shared_task(bind=True, max_retries=3)
def send_email_verification_otp(self, email, otp):
    """Send email verification OTP"""
    try:
        subject = 'Email Verification OTP'
        message = f'Your email verification OTP is: {otp}\n\nValid for 10 minutes.'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        logger.info(f'Verification email sent to {email}')
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f'Email failed for {email}: {e}')
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_welcome_email(user_id):
    """Send welcome email after registration"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        subject = 'Welcome to Our Store!'
        message = f'Hello {user.full_name or user.mobile},\n\nThank you for joining us!'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f'Welcome email sent to {user.email}')
        
    except Exception as e:
        logger.error(f'Welcome email failed: {e}')


@shared_task
def send_order_confirmation_email(order_id):
    """Send order confirmation email"""
    try:
        from .models import Order
        order = Order.objects.select_related('user').get(id=order_id)
        
        subject = f'Order Confirmation - {order.order_number}'
        message = f'''
        Hello {order.user.full_name},
        
        Your order {order.order_number} has been placed successfully!
        
        Order Total: ₹{order.total}
        
        Thank you for shopping with us!
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
        
        logger.info(f'Order confirmation sent for {order.order_number}')
        
    except Exception as e:
        logger.error(f'Order confirmation email failed: {e}')


# ==================== Cache Warming Tasks ====================
@shared_task
def warm_product_cache():
    """Warm up product cache"""
    try:
        from .models import Product
        from django.core.cache import cache
        
        products = Product.objects.filter(available=True).select_related('category')[:50]
        
        for product in products:
            cache_key = f'product_{product.id}'
            cache.set(cache_key, product, 3600)
        
        logger.info(f'Warmed cache for {products.count()} products')
        
    except Exception as e:
        logger.error(f'Cache warming failed: {e}')


@shared_task
def update_popular_searches():
    """Update popular searches cache"""
    try:
        from django.core.cache import cache
        
        search_counts = cache.get('search_counts', {})
        if search_counts:
            popular = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            popular_queries = [query for query, count in popular]
            cache.set('popular_searches', popular_queries, 86400)
            
            logger.info(f'Updated popular searches: {len(popular_queries)} queries')
        
    except Exception as e:
        logger.error(f'Popular searches update failed: {e}')


# ==================== Inventory Tasks ====================
@shared_task
def check_low_stock():
    """Check and alert for low stock products"""
    try:
        from .models import Product
        
        low_stock = Product.objects.filter(stock__lte=5, available=True)
        
        if low_stock.exists():
            message = f'{low_stock.count()} products are low on stock'
            logger.warning(message)
            # Send email to admin
            send_mail(
                'Low Stock Alert',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        
    except Exception as e:
        logger.error(f'Low stock check failed: {e}')