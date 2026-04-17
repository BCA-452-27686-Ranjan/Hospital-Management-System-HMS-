"""
Custom middleware for HMS production deployment
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        if hasattr(settings, 'SECURITY_HEADERS'):
            for header, value in settings.SECURITY_HEADERS.items():
                response[header] = value
        
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor application performance and log slow queries
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        if not getattr(settings, 'ENABLE_PERFORMANCE_MONITORING', False):
            return self.get_response(request)
        
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log slow requests
        threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 1.0)
        if processing_time > threshold:
            logger.warning(
                f'Slow request: {request.method} {request.get_full_path()} '
                f'took {processing_time:.2f}s'
            )
        
        # Add performance headers
        response['X-Response-Time'] = str(processing_time)
        response['X-Process-Time'] = str(time.time())
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all requests for monitoring and debugging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        # Skip logging for static files and media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Log request details
        logger.info(
            f'{request.method} {request.get_full_path()} - '
            f'IP: {self.get_client_ip(request)} - '
            f'User-Agent: {request.META.get("HTTP_USER_AGENT", "Unknown")} - '
            f'Status: {getattr(request, "status_code", "Unknown")}'
        )
        
        response = self.get_response(request)
        
        # Store status code for performance middleware
        request.status_code = response.status_code
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Display maintenance page when site is under maintenance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if getattr(settings, 'MAINTENANCE_MODE', False):
            # Allow access to admin panel during maintenance
            if request.path.startswith('/admin/') or request.path.startswith('/dashboard/admin/'):
                return self.get_response(request)
            
            # Return maintenance page
            return HttpResponse(
                '''
                <html>
                <head>
                    <title>Site Under Maintenance</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
                        .maintenance-icon { font-size: 72px; color: #f39c12; }
                        h1 { color: #333; }
                        p { color: #666; }
                    </style>
                </head>
                <body>
                    <div class="maintenance-icon">⚙️</div>
                    <h1>Site Under Maintenance</h1>
                    <p>We're currently performing scheduled maintenance.</p>
                    <p>We'll be back shortly. Thank you for your patience!</p>
                </body>
                </html>
                ''',
                status=503,
                content_type='text/html'
            )
        
        return self.get_response(request)
