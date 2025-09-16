from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.decorators import require_role, audit_action
from core_hr.models import Employee, Attendance, LeaveRequest, Payroll, LeaveBalance, WorkHours


@login_required
@require_role('employee')
@audit_action('employee_dashboard_access')
def dashboard(request):
    """Employee Dashboard with Live Data and optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        leave_balance = employee.get_leave_balance()

        context = {
            'employee': employee,
            'hours_worked': employee.get_current_month_hours(),
            'leave_balance': leave_balance.annual_leave_remaining,
            'pending_requests': employee.get_pending_leave_requests(),
            'attendance_percentage': employee.get_attendance_percentage(),
            'current_date': timezone.now().date(),
            'leave_balance_obj': leave_balance,
        }
    except Employee.DoesNotExist:
        context = {
            'employee': None,
            'hours_worked': 0,
            'leave_balance': 0,
            'pending_requests': 0,
            'attendance_percentage': 0,
            'current_date': timezone.now().date(),
            'leave_balance_obj': None,
            'error': 'Employee profile not found. Please contact HR.'
        }
    except Exception as e:
        context = {
            'employee': None,
            'hours_worked': 0,
            'leave_balance': 0,
            'pending_requests': 0,
            'attendance_percentage': 0,
            'current_date': timezone.now().date(),
            'leave_balance_obj': None,
            'error': 'Unable to load dashboard data.'
        }

    return render(request, 'employee_portal/dashboard.html', context)


@login_required
@require_role('employee')
def profile(request):
    """Employee Profile Management with optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        return render(request, 'employee_portal/profile.html', {
            'employee': employee
        })
    except Employee.DoesNotExist:
        return render(request, 'employee_portal/profile.html', {
            'employee': None,
            'error': 'Employee profile not found. Please contact HR.'
        })
    except Exception as e:
        return render(request, 'employee_portal/profile.html', {
            'employee': None,
            'error': 'Unable to load profile data.'
        })


@login_required
@require_role('employee')
def attendance(request):
    """Employee Attendance View with Statistics and optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        # Get all attendance records with optimized query
        all_attendance = Attendance.objects.filter(employee=employee).order_by('-date')

        # Calculate statistics from all records using database aggregation
        from django.db.models import Sum, Count, Q
        stats = all_attendance.aggregate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status__in=['present', 'late'])),
            late_days=Count('id', filter=Q(status='late')),
            absent_days=Count('id', filter=Q(status='absent'))
        )

        # Get last 30 days for display
        attendance_records = all_attendance[:30]

        # Calculate total hours more efficiently
        attendance_dates = [record.date for record in attendance_records]
        total_hours = WorkHours.objects.filter(
            employee=employee,
            date__in=attendance_dates
        ).aggregate(total=Sum('total_hours'))['total'] or 0

        context = {
            'attendance_records': attendance_records,
            'total_days': stats['total_days'] or 0,
            'present_days': stats['present_days'] or 0,
            'late_days': stats['late_days'] or 0,
            'absent_days': stats['absent_days'] or 0,
            'total_hours': total_hours,
            'attendance_percentage': employee.get_attendance_percentage(),
        }
    except Employee.DoesNotExist:
        context = {
            'attendance_records': [],
            'total_days': 0,
            'present_days': 0,
            'late_days': 0,
            'absent_days': 0,
            'total_hours': 0,
            'attendance_percentage': 0,
            'error': 'Employee profile not found.'
        }
    except Exception as e:
        context = {
            'attendance_records': [],
            'total_days': 0,
            'present_days': 0,
            'late_days': 0,
            'absent_days': 0,
            'total_hours': 0,
            'attendance_percentage': 0,
            'error': 'Unable to load attendance data.'
        }

    return render(request, 'employee_portal/attendance.html', context)


@login_required
@require_role('employee')
def leave_requests(request):
    """Employee Leave Requests with optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        leave_requests = LeaveRequest.objects.filter(
            employee=employee
        ).order_by('-created_at')

        return render(request, 'employee_portal/leave_requests.html', {
            'leave_requests': leave_requests
        })
    except Employee.DoesNotExist:
        return render(request, 'employee_portal/leave_requests.html', {
            'leave_requests': [],
            'error': 'Employee profile not found.'
        })
    except Exception as e:
        return render(request, 'employee_portal/leave_requests.html', {
            'leave_requests': [],
            'error': 'Unable to load leave requests.'
        })


@login_required
@require_role('employee')
def payslips(request):
    """Employee Payslips with Real Data and optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        payslips = Payroll.objects.filter(
            employee=employee
        ).order_by('-pay_period_end')[:12]  # Last 12 months

        # Calculate YTD totals using database aggregation
        current_year = timezone.now().year
        from django.db.models import Sum
        ytd_totals = Payroll.objects.filter(
            employee=employee,
            pay_period_end__year=current_year
        ).aggregate(
            ytd_gross=Sum('gross_pay'),
            ytd_deductions=Sum('total_deductions'),
            ytd_net=Sum('net_pay')
        )

        context = {
            'payslips': payslips,
            'ytd_gross': ytd_totals['ytd_gross'] or 0,
            'ytd_deductions': ytd_totals['ytd_deductions'] or 0,
            'ytd_net': ytd_totals['ytd_net'] or 0,
            'current_year': current_year,
        }
    except Employee.DoesNotExist:
        context = {
            'payslips': [],
            'ytd_gross': 0,
            'ytd_deductions': 0,
            'ytd_net': 0,
            'current_year': timezone.now().year,
            'error': 'Employee profile not found.'
        }
    except Exception as e:
        context = {
            'payslips': [],
            'ytd_gross': 0,
            'ytd_deductions': 0,
            'ytd_net': 0,
            'current_year': timezone.now().year,
            'error': 'Unable to load payslip data.'
        }

    return render(request, 'employee_portal/payslips.html', context)


# Live Update API Endpoints
@login_required
@require_role('employee')
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """API endpoint for live dashboard statistics with optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        leave_balance = employee.get_leave_balance()

        data = {
            'hours_worked': float(employee.get_current_month_hours()),
            'leave_balance': leave_balance.annual_leave_remaining,
            'pending_requests': employee.get_pending_leave_requests(),
            'attendance_percentage': employee.get_attendance_percentage(),
            'sick_leave_remaining': leave_balance.sick_leave_remaining,
            'personal_leave_remaining': leave_balance.personal_leave_remaining,
        }
    except Employee.DoesNotExist:
        data = {
            'error': 'Employee profile not found',
            'hours_worked': 0,
            'leave_balance': 0,
            'pending_requests': 0,
            'attendance_percentage': 0,
            'sick_leave_remaining': 0,
            'personal_leave_remaining': 0,
        }
    except Exception as e:
        data = {
            'error': 'Unable to load dashboard statistics',
            'hours_worked': 0,
            'leave_balance': 0,
            'pending_requests': 0,
            'attendance_percentage': 0,
            'sick_leave_remaining': 0,
            'personal_leave_remaining': 0,
        }

    return JsonResponse(data)


@login_required
@require_role('employee')
@require_http_methods(["GET"])
def api_recent_attendance(request):
    """API endpoint for recent attendance data with optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        attendance_records = Attendance.objects.filter(
            employee=employee
        ).order_by('-date')[:7]  # Last 7 days

        data = []
        for record in attendance_records:
            data.append({
                'date': record.date.strftime('%Y-%m-%d'),
                'status': record.status,
                'clock_in': record.clock_in.strftime('%H:%M') if record.clock_in else None,
                'clock_out': record.clock_out.strftime('%H:%M') if record.clock_out else None,
                'total_hours': float(record.total_hours) if record.total_hours else 0,
            })
    except Employee.DoesNotExist:
        data = []
        return JsonResponse({
            'attendance_records': data,
            'error': 'Employee profile not found'
        })
    except Exception as e:
        data = []
        return JsonResponse({
            'attendance_records': data,
            'error': 'Unable to load attendance data'
        })

    return JsonResponse({'attendance_records': data})


@login_required
@require_role('employee')
@require_http_methods(["POST"])
def api_update_profile(request):
    """API endpoint for updating employee profile with optimized queries"""
    try:
        # Use select_related to optimize employee data access
        employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        # Update allowed fields with validation
        updated_fields = []
        if 'phone' in request.POST:
            phone = request.POST['phone'].strip()
            if len(phone) <= 20:  # Validate phone length
                employee.phone = phone
                updated_fields.append('phone')

        if 'address' in request.POST:
            address = request.POST['address'].strip()
            if len(address) <= 500:  # Validate address length
                employee.address = address
                updated_fields.append('address')

        if updated_fields:
            employee.save(update_fields=updated_fields)  # Only update changed fields

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'updated_fields': updated_fields
        })
    except Employee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee profile not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        })
