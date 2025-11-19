# your_app/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class MobileBackend(ModelBackend):
    """
    Custom authentication backend for mobile-based login
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if 'mobile' is passed instead of 'username'
        mobile = kwargs.get('mobile', username)
        
        if mobile is None:
            return None
        
        try:
            # Try to find user by mobile
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            return None
        
        # Check password
        if user.check_password(password):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None