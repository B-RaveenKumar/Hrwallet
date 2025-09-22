from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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


def company_admin_login(request):
    """Company Admin Login Page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user and user.role in ['super_admin', 'hr_manager']:
                login(request, user)
                messages.success(request, f'Welcome, {user.get_full_name()}!')
                return redirect('admin_panel:company_admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials or insufficient permissions.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'admin_panel/company_admin_login.html')


@login_required
def company_admin_dashboard(request):
    """Company Admin Dashboard - Django Admin-like interface"""
    if request.user.role not in ['super_admin', 'hr_manager']:
        messages.error(request, 'Access denied. You do not have permission to access this area.')
        return redirect('accounts:login')
    
    try:
        # Get comprehensive stats for the admin dashboard
        if request.user.role == 'super_admin':
            # Super admin sees all data
            companies = Company.objects.all()
            users = User.objects.all()
            employees = Employee.objects.all()
            departments = Department.objects.all()
        else:
            # HR managers see only their company data
            companies = Company.objects.filter(id=request.user.company.id) if request.user.company else Company.objects.none()
            users = User.objects.filter(company=request.user.company) if request.user.company else User.objects.none()
            employees = Employee.objects.filter(company=request.user.company) if request.user.company else Employee.objects.none()
            departments = Department.objects.filter(company=request.user.company) if request.user.company else Department.objects.none()
        
        context = {
            'user': request.user,
            'is_super_admin': request.user.role == 'super_admin',
            'companies': companies,
            'users': users,
            'employees': employees,
            'departments': departments,
            'stats': {
                'total_companies': companies.count(),
                'total_users': users.count(),
                'total_employees': employees.count(),
                'total_departments': departments.count(),
                'active_employees': employees.filter(is_active=True).count(),
                'hr_managers': users.filter(role='hr_manager').count(),
            }
        }
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        context = {
            'user': request.user,
            'is_super_admin': request.user.role == 'super_admin',
            'companies': Company.objects.none(),
            'users': User.objects.none(),
            'employees': Employee.objects.none(),
            'departments': Department.objects.none(),
            'stats': {
                'total_companies': 0,
                'total_users': 0,
                'total_employees': 0,
                'total_departments': 0,
                'active_employees': 0,
                'hr_managers': 0,
            }
        }
    
    return render(request, 'admin_panel/company_admin_dashboard.html', context)
