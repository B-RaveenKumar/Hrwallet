from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from accounts.decorators import require_role, audit_action
from core_hr.models import Employee, Department, LeaveRequest, Attendance, BiometricDevice, BiometricEvent


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
        # Filter by company for security
        employees = Employee.objects.filter(
            is_active=True, 
            company=request.user.company
        ).select_related(
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
def departments(request):
    """Departments management page (uses APIs for data)."""
    return render(request, 'hr_dashboard/departments.html')


@login_required
@require_role('hr_manager')
def biometric_monitor(request):
    """Read-only Biometric monitoring page for HR Managers with real-time device status."""
    devices = BiometricDevice.objects.filter(company=request.user.company)
    return render(request, 'hr_dashboard/biometric.html', {
        'devices': devices
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
    """Attendance Overview with filters and company scoping"""
    try:
        target_date_str = (request.GET.get('date') or '').strip()
        try:
            target_date = timezone.datetime.strptime(target_date_str, '%Y-%m-%d').date() if target_date_str else timezone.now().date()
        except Exception:
            target_date = timezone.now().date()

        status_filter = (request.GET.get('status') or '').strip().lower()
        dept_id = (request.GET.get('department_id') or '').strip()
        q = (request.GET.get('q') or '').strip()

        employees_qs = Employee.objects.filter(is_active=True, company=request.user.company).select_related('user', 'department', 'company')
        if dept_id:
            employees_qs = employees_qs.filter(department_id=dept_id)
        if q:
            employees_qs = employees_qs.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(employee_id__icontains=q))
        employees_qs = employees_qs.order_by('employee_id')

        attendance_qs = Attendance.objects.filter(employee__company=request.user.company, date=target_date).select_related('employee__user', 'employee__department')
        if status_filter in ['present', 'absent', 'late', 'half_day']:
            attendance_qs = attendance_qs.filter(status=status_filter)
        attendance_by_emp = {a.employee_id: a for a in attendance_qs}

        rows = []
        for emp in employees_qs:
            rows.append({'employee': emp, 'attendance': attendance_by_emp.get(emp.id)})

        departments = Department.objects.filter(company=request.user.company, is_active=True).order_by('name')
        present_today = Attendance.objects.filter(employee__company=request.user.company, date=target_date, status__in=['present', 'late']).count()

        return render(request, 'hr_dashboard/attendance.html', {
            'rows': rows,
            'departments': departments,
            'present_today': present_today,
            'today': target_date,
            'filters': {
                'date': target_date.strftime('%Y-%m-%d'),
                'status': status_filter,
                'department_id': dept_id,
                'q': q,
            }
        })
    except Exception as e:
        return render(request, 'hr_dashboard/attendance.html', {
            'rows': [],
            'departments': Department.objects.none(),
            'today': timezone.now().date(),
            'filters': {},
            'error': 'Unable to load attendance data.'
        })


@login_required
@require_role('hr_manager')
def create_employee(request):
    """Create Employee form page"""
    return render(request, 'hr_dashboard/create_employee.html')


from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q
import json
import csv
from io import StringIO


@login_required
@require_role('hr_manager')
@require_http_methods(["PATCH"])
def change_leave_status_api(request, pk):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_status = (data.get('status') or '').lower()
    if new_status not in ['approved', 'rejected']:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    leave = get_object_or_404(
        LeaveRequest.objects.select_related('employee__user', 'employee__company'),
        pk=pk,
        employee__company=request.user.company
    )

    if leave.status != 'pending':
        return JsonResponse({'error': 'Only pending requests can be updated'}, status=400)

    with transaction.atomic():
        leave.status = new_status
        leave.approved_by = request.user
        leave.save()

        # Adjust leave balance on approval
        if new_status == 'approved':
            lb = None
            try:
                lb = leave.employee.leavebalance
            except Exception:
                lb = None
            if lb:
                if leave.leave_type == 'annual':
                    lb.annual_leave_used = (lb.annual_leave_used or 0) + leave.days_requested
                elif leave.leave_type == 'sick':
                    lb.sick_leave_used = (lb.sick_leave_used or 0) + leave.days_requested
                elif leave.leave_type == 'personal':
                    lb.personal_leave_used = (lb.personal_leave_used or 0) + leave.days_requested
                lb.save()

    return JsonResponse({'success': True})


@login_required
@require_role('hr_manager')
@require_http_methods(["POST"])
def bulk_change_leaves_api(request):
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    ids = data.get('ids') or []
    status_target = (data.get('status') or '').lower()
    if not isinstance(ids, list) or status_target not in ['approved', 'rejected']:
        return JsonResponse({'error': 'ids (list) and valid status are required'}, status=400)

    leaves = LeaveRequest.objects.filter(
        id__in=ids, status='pending', employee__company=request.user.company
    )

    updated = 0
    with transaction.atomic():
        for leave in leaves.select_related('employee'):
            leave.status = status_target
            leave.approved_by = request.user
            leave.save()
            updated += 1
            if status_target == 'approved':
                try:
                    lb = leave.employee.leavebalance
                    if leave.leave_type == 'annual':
                        lb.annual_leave_used = (lb.annual_leave_used or 0) + leave.days_requested
                    elif leave.leave_type == 'sick':
                        lb.sick_leave_used = (lb.sick_leave_used or 0) + leave.days_requested
                    elif leave.leave_type == 'personal':
                        lb.personal_leave_used = (lb.personal_leave_used or 0) + leave.days_requested
                    lb.save()
                except Exception:
                    pass

    return JsonResponse({'success': True, 'updated': updated})


@login_required
@require_role('hr_manager')
@require_http_methods(["GET"])
def export_leaves_api(request):
    qs = LeaveRequest.objects.filter(employee__company=request.user.company).select_related('employee__user', 'employee__department')

    status_filter = (request.GET.get('status') or '').lower()
    if status_filter in ['pending', 'approved', 'rejected']:
        qs = qs.filter(status=status_filter)

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(employee__user__first_name__icontains=q) |
            Q(employee__user__last_name__icontains=q) |
            Q(employee__employee_id__icontains=q)
        )

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Employee', 'Employee ID', 'Department', 'Type', 'Start', 'End', 'Days', 'Status', 'Submitted'])
    for leave in qs.order_by('-created_at'):
        writer.writerow([
            leave.employee.user.get_full_name(),
            leave.employee.employee_id,
            getattr(getattr(leave.employee, 'department', None), 'name', ''),
            leave.leave_type,
            leave.start_date.strftime('%Y-%m-%d'),
            leave.end_date.strftime('%Y-%m-%d'),
            leave.days_requested,
            leave.status,
            leave.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    resp = HttpResponse(buffer.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="leave_requests.csv"'
    return resp

# -------------------- Attendance APIs --------------------
from decimal import Decimal
from datetime import datetime, date, time as dt_time, timedelta


def _get_employee_for_company_or_404(request, employee_pk):
    return get_object_or_404(Employee.objects.select_related('company'), pk=employee_pk, company=request.user.company)


def _parse_date(value):
    if not value:
        return timezone.now().date()
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except Exception:
        return timezone.now().date()


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%H:%M').time()
    except Exception:
        return None


def _recompute_total_hours(att):
    if att.clock_in and att.clock_out:
        dt_in = datetime.combine(att.date, att.clock_in)
        dt_out = datetime.combine(att.date, att.clock_out)
        if dt_out < dt_in:
            dt_out = dt_out + timedelta(days=1)
        delta = dt_out - dt_in
        if att.break_duration:
            delta -= att.break_duration
        hours = Decimal(delta.total_seconds() / 3600.0).quantize(Decimal('0.01'))
        att.total_hours = hours
    return att


@login_required
@require_role('hr_manager')
@require_http_methods(["POST"])
def attendance_clock_in_api(request):
    data = json.loads(request.body or '{}')
    employee_pk = data.get('employee_pk')
    if not employee_pk:
        return JsonResponse({'error': 'employee_pk is required'}, status=400)
    target_date = _parse_date(data.get('date'))
    t = _parse_time(data.get('time')) or timezone.now().time()

    emp = _get_employee_for_company_or_404(request, employee_pk)
    att, _created = Attendance.objects.get_or_create(employee=emp, date=target_date)
    att.clock_in = t
    # simple status heuristic
    att.status = att.status or 'present'
    att = _recompute_total_hours(att)
    att.save()
    return JsonResponse({'success': True})


@login_required
@require_role('hr_manager')
@require_http_methods(["POST"])
def attendance_clock_out_api(request):
    data = json.loads(request.body or '{}')
    employee_pk = data.get('employee_pk')
    if not employee_pk:
        return JsonResponse({'error': 'employee_pk is required'}, status=400)
    target_date = _parse_date(data.get('date'))
    t = _parse_time(data.get('time')) or timezone.now().time()

    emp = _get_employee_for_company_or_404(request, employee_pk)
    att, _created = Attendance.objects.get_or_create(employee=emp, date=target_date)
    att.clock_out = t
    att = _recompute_total_hours(att)
    att.save()
    return JsonResponse({'success': True})


@login_required
@require_role('hr_manager')
@require_http_methods(["PATCH"])
def update_attendance_api(request):
    data = json.loads(request.body or '{}')
    employee_pk = data.get('employee_pk')
    if not employee_pk:
        return JsonResponse({'error': 'employee_pk is required'}, status=400)
    target_date = _parse_date(data.get('date'))

    emp = _get_employee_for_company_or_404(request, employee_pk)
    att, _ = Attendance.objects.get_or_create(employee=emp, date=target_date)

    ci = _parse_time(data.get('clock_in'))
    co = _parse_time(data.get('clock_out'))
    status = data.get('status')
    notes = data.get('notes')

    if ci is not None:
        att.clock_in = ci
    if co is not None:
        att.clock_out = co
    if status in ['present', 'absent', 'late', 'half_day']:
        att.status = status
    if notes is not None:
        att.notes = notes

    att = _recompute_total_hours(att)
    att.save()
    return JsonResponse({'success': True})


@login_required
@require_role('hr_manager')
@require_http_methods(["GET"])
def export_attendance_api(request):
    target_date = _parse_date(request.GET.get('date'))
    qs = Attendance.objects.filter(employee__company=request.user.company, date=target_date).select_related('employee__user', 'employee__department')

    status_filter = (request.GET.get('status') or '').lower()
    if status_filter in ['present', 'absent', 'late', 'half_day']:
        qs = qs.filter(status=status_filter)

    dept_id = request.GET.get('department_id')
    if dept_id:
        qs = qs.filter(employee__department_id=dept_id)

    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(employee__user__first_name__icontains=q) |
            Q(employee__user__last_name__icontains=q) |
            Q(employee__employee_id__icontains=q)
        )

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Employee', 'Employee ID', 'Department', 'Date', 'Clock In', 'Clock Out', 'Hours', 'Status'])
    for att in qs.order_by('employee__employee_id'):
        writer.writerow([
            att.employee.user.get_full_name(),
            att.employee.employee_id,
            getattr(getattr(att.employee, 'department', None), 'name', ''),
            att.date.strftime('%Y-%m-%d'),
            att.clock_in.strftime('%H:%M') if att.clock_in else '',
            att.clock_out.strftime('%H:%M') if att.clock_out else '',
            str(att.total_hours or ''),
            att.status
        ])

    resp = HttpResponse(buffer.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="attendance_{target_date.strftime("%Y%m%d")}.csv"'
    return resp


@login_required
@require_role('hr_manager')
def biometric_attendance_dashboard(request):
    """Biometric Attendance section with filters, edit, bulk edit, and distinction from manual entries."""
    # Filters
    device_id = request.GET.get('device_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    employee_id = request.GET.get('employee_id')
    status = request.GET.get('status')
    events = BiometricEvent.objects.filter(company=request.user.company)
    if device_id:
        events = events.filter(device_id=device_id)
    if date_from:
        events = events.filter(timestamp__gte=date_from)
    if date_to:
        events = events.filter(timestamp__lte=date_to)
    if employee_id:
        events = events.filter(device_user_id=employee_id)
    if status:
        events = events.filter(event_type=status)
    events = events.select_related('device', 'attendance').order_by('-timestamp')[:200]
    devices = BiometricDevice.objects.filter(company=request.user.company)
    employees = Employee.objects.filter(company=request.user.company, is_active=True)
    return render(request, 'hr_dashboard/biometric_attendance.html', {
        'events': events,
        'devices': devices,
        'employees': employees,
        'filters': {
            'device_id': device_id,
            'date_from': date_from,
            'date_to': date_to,
            'employee_id': employee_id,
            'status': status,
        }
    })


@login_required
@require_role('hr_manager')
@audit_action('hr_profile_access')
def hr_profile(request):
    """HR Manager Profile Management"""
    try:
        # Get HR manager's employee record
        hr_employee = Employee.objects.select_related(
            'user', 'department', 'company'
        ).get(user=request.user)

        if request.method == 'POST':
            # Handle profile update
            try:
                # Update user information
                user = request.user
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = request.POST.get('email', '').strip()
                user.save()

                # Update employee information
                hr_employee.phone = request.POST.get('phone', '').strip()
                hr_employee.job_title = request.POST.get('job_title', '').strip()
                hr_employee.address = request.POST.get('address', '').strip()
                hr_employee.save()

                messages.success(request, 'Profile updated successfully!')
                return redirect('hr_dashboard:hr_profile')

            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')

        # Get recent activity logs for this HR manager
        from payroll.models import AuditLog
        recent_activities = AuditLog.objects.filter(
            user=request.user
        ).order_by('-timestamp')[:10]

        # Get statistics for HR dashboard
        total_employees = Employee.objects.filter(
            company=request.user.company,
            is_active=True
        ).exclude(user__role='hr_manager').count()

        pending_leaves = LeaveRequest.objects.filter(
            employee__company=request.user.company,
            status='pending'
        ).count()

        today_attendance = Attendance.objects.filter(
            employee__company=request.user.company,
            date=timezone.now().date(),
            status__in=['present', 'late']
        ).count()

        # Get salary information if available
        from payroll.models import EmployeeSalary
        current_salary = EmployeeSalary.objects.filter(
            employee=hr_employee,
            is_active=True,
            status='approved'
        ).order_by('-effective_date').first()

        context = {
            'hr_employee': hr_employee,
            'recent_activities': recent_activities,
            'current_salary': current_salary,
            'stats': {
                'total_employees': total_employees,
                'pending_leaves': pending_leaves,
                'today_attendance': today_attendance,
            }
        }

        return render(request, 'hr_dashboard/hr_profile.html', context)

    except Employee.DoesNotExist:
        messages.error(request, 'HR employee profile not found.')
        return redirect('hr_dashboard:hr_dashboard')
    except Exception as e:
        messages.error(request, f'Error loading profile: {str(e)}')
        return redirect('hr_dashboard:hr_dashboard')

