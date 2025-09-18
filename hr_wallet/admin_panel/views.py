from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from accounts.decorators import require_role, audit_action
from accounts.models import User
from core_hr.models import Employee, Department, Company


@login_required
@require_role('super_admin')
@audit_action('admin_dashboard_access')
def dashboard(request):
    """Super Admin Dashboard with optimized queries"""
    try:
        # Use select_related for recent users to avoid N+1 queries
        recent_users = User.objects.select_related('company').order_by('-date_joined')[:5]

        context = {
            'total_users': User.objects.count(),
            'total_employees': Employee.objects.count(),
            'total_departments': Department.objects.count(),
            'hr_managers': User.objects.filter(role='hr_manager').count(),
            'recent_users': recent_users,
        }
    except Exception as e:
        # Handle database errors gracefully
        context = {
            'total_users': 0,
            'total_employees': 0,
            'total_departments': 0,
            'hr_managers': 0,
            'recent_users': [],
            'error': 'Unable to load dashboard data. Please try again.'
        }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@require_role('super_admin')
def user_management(request):
    """User management view with real-time functionality"""
    context = {
        'page_title': 'User Management',
        'user': request.user,
    }
    return render(request, 'admin_panel/user_management.html', context)


@login_required
@require_role('super_admin')
def manage_hr_managers(request):
    """Manage HR Managers with optimized queries"""
    try:
        # Use select_related to avoid N+1 queries when accessing company data
        hr_managers = User.objects.filter(role='hr_manager').select_related('company').order_by('-date_joined')
        return render(request, 'admin_panel/hr_managers.html', {
            'hr_managers': hr_managers
        })
    except Exception as e:
        return render(request, 'admin_panel/hr_managers.html', {
            'hr_managers': [],
            'error': 'Unable to load HR managers data.'
        })


@login_required
@require_role('super_admin')
def system_settings(request):
    """System Settings with error handling"""
    try:
        company = Company.objects.first()
        return render(request, 'admin_panel/settings.html', {
            'company': company
        })
    except Exception as e:
        return render(request, 'admin_panel/settings.html', {
            'company': None,
            'error': 'Unable to load system settings.'
        })


@login_required
@require_role('super_admin')
def create_hr_manager(request):
    """Create HR Manager form page"""
    return render(request, 'admin_panel/create_hr.html')


@login_required
@require_role('super_admin')
def audit_logs(request):
    """View Audit Logs"""
    # This would typically fetch from a logging system
    return render(request, 'admin_panel/audit_logs.html')



@login_required
@require_role('super_admin')
def biometric_devices(request):
    """Manage biometric devices and mappings (Super Admin)."""
    return render(request, 'admin_panel/biometric_devices.html')
