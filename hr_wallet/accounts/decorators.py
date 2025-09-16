"""
Security decorators for role-based access control
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
import logging

logger = logging.getLogger(__name__)


def require_role(required_role):
    """
    Decorator to require specific role for view access
    
    Usage:
        @require_role('super_admin')
        def admin_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role != required_role:
                logger.warning(
                    f"Access denied: User {request.user.username} "
                    f"(role: {request.user.role}) attempted to access "
                    f"view requiring role: {required_role}"
                )
                return HttpResponseForbidden(
                    "You don't have permission to access this page."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_roles(*required_roles):
    """
    Decorator to require one of multiple roles for view access
    
    Usage:
        @require_roles('super_admin', 'hr_manager')
        def admin_or_hr_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in required_roles:
                logger.warning(
                    f"Access denied: User {request.user.username} "
                    f"(role: {request.user.role}) attempted to access "
                    f"view requiring roles: {required_roles}"
                )
                return HttpResponseForbidden(
                    "You don't have permission to access this page."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RoleBasedAccessMixin:
    """
    Mixin for class-based views to enforce role-based access
    
    Usage:
        class AdminView(RoleBasedAccessMixin, View):
            required_role = 'super_admin'
            
            def get(self, request):
                ...
    """
    required_role = None
    required_roles = None
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Check single role requirement
        if self.required_role and request.user.role != self.required_role:
            logger.warning(
                f"Access denied: User {request.user.username} "
                f"(role: {request.user.role}) attempted to access "
                f"view requiring role: {self.required_role}"
            )
            return HttpResponseForbidden(
                "You don't have permission to access this page."
            )
        
        # Check multiple roles requirement
        if self.required_roles and request.user.role not in self.required_roles:
            logger.warning(
                f"Access denied: User {request.user.username} "
                f"(role: {request.user.role}) attempted to access "
                f"view requiring roles: {self.required_roles}"
            )
            return HttpResponseForbidden(
                "You don't have permission to access this page."
            )
        
        return super().dispatch(request, *args, **kwargs)


def audit_action(action_type):
    """
    Decorator to log user actions for audit trail
    
    Usage:
        @audit_action('user_login')
        def login_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                logger.info(
                    f"Audit: {action_type} - User: {request.user.username} "
                    f"(role: {request.user.role}) - IP: {request.META.get('REMOTE_ADDR')}"
                )
            response = view_func(request, *args, **kwargs)
            return response
        return _wrapped_view
    return decorator
