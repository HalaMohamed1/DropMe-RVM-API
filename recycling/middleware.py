import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

logger = logging.getLogger('security')

class SecurityMiddleware(MiddlewareMixin):
    """Enhanced security middleware for production"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Rate limiting by IP
        client_ip = self.get_client_ip(request)
        
        # Different limits for different endpoints
        if request.path.startswith('/api/deposits/'):
            limit_key = f"deposit_limit_{client_ip}"
            if cache.get(limit_key, 0) >= 10:  # 10 deposits per minute
                logger.warning(f"Deposit rate limit exceeded for IP: {client_ip}")
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                }, status=429)
            cache.set(limit_key, cache.get(limit_key, 0) + 1, 60)
        
        elif request.path.startswith('/api/auth/'):
            limit_key = f"auth_limit_{client_ip}"
            if cache.get(limit_key, 0) >= 5:  # 5 auth attempts per minute
                logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
                return JsonResponse({
                    'error': 'Too many authentication attempts. Please try again later.',
                    'retry_after': 300
                }, status=429)
            cache.set(limit_key, cache.get(limit_key, 0) + 1, 300)
        
        # General API rate limiting
        general_limit_key = f"api_limit_{client_ip}"
        if cache.get(general_limit_key, 0) >= 100:  # 100 requests per minute
            logger.warning(f"General API rate limit exceeded for IP: {client_ip}")
            return JsonResponse({
                'error': 'API rate limit exceeded',
                'retry_after': 60
            }, status=429)
        cache.set(general_limit_key, cache.get(general_limit_key, 0) + 1, 60)
        
        return None
    
    def get_client_ip(self, request):
        """Get real client IP considering proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PerformanceMiddleware(MiddlewareMixin):
    """Monitor API performance and log slow requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 2.0:  # 2 seconds threshold
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
            
            # Add performance headers
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class TokenValidationMiddleware(MiddlewareMixin):
    """Enhanced token validation with blacklisting"""
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            
            # Check if token is blacklisted
            if cache.get(f"blacklisted_token_{token_key}"):
                logger.warning(f"Blacklisted token used: {token_key[:10]}...")
                return JsonResponse({
                    'error': 'Token has been invalidated'
                }, status=401)
            
            # Check token expiry (if implemented)
            try:
                token = Token.objects.get(key=token_key)
                # Add custom token expiry logic here if needed
            except Token.DoesNotExist:
                pass
        
        return None
