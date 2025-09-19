"""
Security middleware for role-based access control
"""
import logging
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control at URL level
    """
    
    # URL patterns that require specific roles
    ROLE_URL_PATTERNS = {
        'super_admin': [
            '/admin-panel/',
        ],
        'hr_manager': [
            '/hr-dashboard/',
        ],
        'employee': [
            '/employee-portal/',
        ]
    }
    
    # URLs that don't require authentication
    PUBLIC_URLS = [
        '/accounts/company-selection/',
        '/accounts/login/',
        '/accounts/logout/',
        '/login/',
        '/logout/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Skip middleware for public URLs
        if any(request.path.startswith(url) for url in self.PUBLIC_URLS):
            return None
        
        # Skip middleware for unauthenticated users (let login_required handle it)
        if not request.user.is_authenticated:
            return None
        
        # Check role-based access
        user_role = request.user.role
        
        # Check if user is trying to access a role-restricted URL
        for role, url_patterns in self.ROLE_URL_PATTERNS.items():
            for pattern in url_patterns:
                if request.path.startswith(pattern):
                    if user_role != role:
                        logger.warning(
                            f"Access denied by middleware: User {request.user.username} "
                            f"(role: {user_role}) attempted to access {request.path} "
                            f"which requires role: {role}"
                        )
                        return HttpResponseForbidden(
                            "You don't have permission to access this page."
                        )
        
        return None


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Middleware to log security-related events
    """
    
    def process_request(self, request):
        # Log authentication attempts and access patterns
        if request.user.is_authenticated:
            # Log access to sensitive areas
            sensitive_paths = ['/admin-panel/', '/hr-dashboard/', '/employee-portal/']
            if any(request.path.startswith(path) for path in sensitive_paths):
                logger.info(
                    f"Access: {request.path} - User: {request.user.username} "
                    f"(role: {request.user.role}) - IP: {request.META.get('REMOTE_ADDR')} "
                    f"- User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
                )
        
        return None
    
    def process_response(self, request, response):
        # Log failed access attempts (403 responses)
        if response.status_code == 403 and request.user.is_authenticated:
            logger.warning(
                f"403 Forbidden: {request.path} - User: {request.user.username} "
                f"(role: {request.user.role}) - IP: {request.META.get('REMOTE_ADDR')}"
            )
        
        return response
