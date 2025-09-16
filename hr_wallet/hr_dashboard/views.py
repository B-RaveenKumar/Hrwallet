from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from accounts.decorators import require_role, audit_action
from core_hr.models import Employee, Department, LeaveRequest, Attendance


@login_required
@require_role('hr_manager')
@audit_action('hr_dashboard_access')
def dashboard(request):
    """HR Manager Dashboard with optimized queries"""
    try:
        # Use select_related to optimize queries for related objects
        recent_leave_requests = LeaveRequest.objects.select_related(
            'employee__user', 'employee__department'
        ).order_by('-created_at')[:5]

        recent_employees = Employee.objects.select_related(
            'user', 'department', 'company'
        ).order_by('-hire_date')[:5]

        context = {
            'total_employees': Employee.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.count(),
            'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
            'employees_present_today': Attendance.objects.filter(
                date=timezone.now().date(),
                status='present'
            ).count(),
            'recent_leave_requests': recent_leave_requests,
            'recent_employees': recent_employees,
        }
    except Exception as e:
        # Handle database errors gracefully
        context = {
            'total_employees': 0,
            'total_departments': 0,
            'pending_leaves': 0,
            'employees_present_today': 0,
            'recent_leave_requests': [],
            'recent_employees': [],
            'error': 'Unable to load dashboard data. Please try again.'
        }
    return render(request, 'hr_dashboard/dashboard.html', context)


@login_required
@require_role('hr_manager')
def manage_employees(request):
    """Manage Employees with optimized queries and error handling"""
    try:
        # Use select_related for all related objects to avoid N+1 queries
        employees = Employee.objects.filter(is_active=True).select_related(
            'user', 'department', 'company'
        ).order_by('employee_id')

        return render(request, 'hr_dashboard/employees.html', {
            'employees': employees
        })
    except Exception as e:
        return render(request, 'hr_dashboard/employees.html', {
            'employees': [],
            'error': 'Unable to load employee data.'
        })


@login_required
@require_role('hr_manager')
def leave_approvals(request):
    """Leave Approval Management with optimized queries"""
    try:
        # Use select_related for all related objects
        pending_leaves = LeaveRequest.objects.filter(status='pending').select_related(
            'employee__user', 'employee__department', 'employee__company'
        ).order_by('-created_at')

        return render(request, 'hr_dashboard/leave_approvals.html', {
            'pending_leaves': pending_leaves
        })
    except Exception as e:
        return render(request, 'hr_dashboard/leave_approvals.html', {
            'pending_leaves': [],
            'error': 'Unable to load leave requests.'
        })


@login_required
@require_role('hr_manager')
def attendance_overview(request):
    """Attendance Overview with optimized queries"""
    try:
        today = timezone.now().date()

        # Use select_related for all related objects to avoid N+1 queries
        employees = Employee.objects.filter(is_active=True).select_related(
            'user', 'department', 'company'
        ).order_by('employee_id')

        attendance_data = Attendance.objects.filter(date=today).select_related(
            'employee__user', 'employee__department'
        ).order_by('employee__employee_id')

        return render(request, 'hr_dashboard/attendance.html', {
            'employees': employees,
            'attendance_data': attendance_data,
            'today': today
        })
    except Exception as e:
        return render(request, 'hr_dashboard/attendance.html', {
            'employees': [],
            'attendance_data': [],
            'today': timezone.now().date(),
            'error': 'Unable to load attendance data.'
        })


@login_required
@require_role('hr_manager')
def create_employee(request):
    """Create Employee form page"""
    return render(request, 'hr_dashboard/create_employee.html')
