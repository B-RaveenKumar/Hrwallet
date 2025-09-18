"""
URL configuration for HR Wallet project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.http import HttpResponse

def root_redirect(request):
    """Redirect root URL directly to login or dashboard based on user state"""
    if request.user.is_authenticated:
        try:
            return redirect(request.user.get_dashboard_url())
        except Exception:
            return redirect('accounts:login')
    return redirect('accounts:login')

def favicon_view(request):
    """Return empty favicon to prevent 404 errors"""
    return HttpResponse(status=204)  # No Content

urlpatterns = [
    # Root redirect
    path('', root_redirect, name='root'),

    # Favicon
    path('favicon.ico', favicon_view, name='favicon'),

    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Legacy login/logout redirects
    path('login/', lambda request: redirect('accounts:login')),
    path('logout/', lambda request: redirect('accounts:logout')),

    # Core HR
    path('', include('core_hr.urls')),

    # Role-based dashboards
    path('admin-panel/', include('admin_panel.urls')),
    path('hr-dashboard/', include('hr_dashboard.urls')),
    path('employee-portal/', include('employee_portal.urls')),

    # Profile Management API
    path('api/', include('profile_api.urls')),

    # New apps
    path('payroll/', include('payroll.urls')),
    path('performance/', include('performance.urls')),
    path('notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
