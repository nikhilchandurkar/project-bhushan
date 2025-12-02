from django.shortcuts import redirect
from django.urls import reverse

class ProfileCompletionMiddleware:
    """
    Middleware to redirect authenticated users with incomplete profiles
    to the profile completion page.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs that don't require profile completion
        self.exempt_urls = [
            reverse('shop:profile-completion'),
            reverse('shop:logout'),
            reverse('shop:complete-profile'),  # API endpoint
            reverse('shop:api-user-profile'),  # API endpoint
        ]
        
        # URL patterns to exclude (static, media, admin, api)
        self.exempt_patterns = [
            '/static/',
            '/media/',
            '/admin/',
            '/api/',
        ]
    
    def __call__(self, request):
        # Check if user is authenticated and profile is incomplete
        if request.user.is_authenticated:
            if not request.user.profile_completed:
                # Check if current path is exempt
                current_path = request.path
                
                # Skip middleware for exempt URLs
                if current_path not in self.exempt_urls:
                    # Skip middleware for exempt patterns
                    is_exempt_pattern = any(
                        current_path.startswith(pattern) 
                        for pattern in self.exempt_patterns
                    )
                    
                    if not is_exempt_pattern:
                        # Redirect to profile completion
                        return redirect('shop:profile-completion')
        
        response = self.get_response(request)
        return response