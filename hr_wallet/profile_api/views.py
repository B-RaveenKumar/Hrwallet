from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.decorators import require_role, require_roles
from core_hr.models import Employee, Department, LeaveBalance, Attendance, BiometricDevice, BiometricEvent, BiometricUserMap
from .serializers import (
    EmployeeCreateSerializer, HRCreateSerializer,
    EmployeeListSerializer, HRListSerializer, DepartmentSerializer,
    BiometricEventSerializer, BiometricEventBulkEditSerializer, BiometricUserMapCorrectionSerializer,
    EmployeeDetailSerializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

from django.db.models import Q
from django.http import HttpResponse
import csv
from datetime import datetime
from datetime import timedelta

from django.utils.dateparse import parse_datetime
import hashlib, hmac, json
import secrets

import time




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def list_departments(request):
    """List departments for the current user's company."""
    qs = Department.objects.filter(company=request.user.company).order_by('name')
    data = DepartmentSerializer(qs, many=True).data
    return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def create_department(request):
    name = (request.data.get('name') or '').strip()
    description = (request.data.get('description') or '').strip()
    manager_id = request.data.get('manager_id')
    if not name:
        return Response({'success': False, 'message': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
    if Department.objects.filter(company=request.user.company, name__iexact=name).exists():
        return Response({'success': False, 'message': 'Department with this name already exists'}, status=status.HTTP_400_BAD_REQUEST)
    dept = Department(company=request.user.company, name=name, description=description)
    # Optional manager assignment
    if manager_id:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            manager = User.objects.get(pk=manager_id, company=request.user.company)
            dept.manager = manager
        except Exception:
            pass
    dept.save()
    return Response({'success': True, 'data': DepartmentSerializer(dept).data}, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def update_department(request, pk):
    try:
        dept = Department.objects.get(pk=pk, company=request.user.company)
    except Department.DoesNotExist:
        return Response({'success': False, 'message': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    name = request.data.get('name')
    description = request.data.get('description')
    manager_id = request.data.get('manager_id')
    is_active = request.data.get('is_active')

    if name is not None:
        name = name.strip()
        if not name:
            return Response({'success': False, 'message': 'Name cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        if Department.objects.filter(company=request.user.company, name__iexact=name).exclude(pk=dept.pk).exists():
            return Response({'success': False, 'message': 'Another department with this name exists'}, status=status.HTTP_400_BAD_REQUEST)
        dept.name = name
    if description is not None:
        dept.description = description
    if manager_id is not None:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            manager = User.objects.get(pk=manager_id, company=request.user.company)
            dept.manager = manager
        except Exception:
            dept.manager = None
    if is_active is not None:
        is_active_bool = is_active if isinstance(is_active, bool) else str(is_active).lower() in ['1', 'true', 'yes']
        dept.is_active = is_active_bool

    dept.save()
    return Response({'success': True, 'data': DepartmentSerializer(dept).data}, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def change_department_status(request, pk):
    try:
        dept = Department.objects.get(pk=pk, company=request.user.company)
    except Department.DoesNotExist:
        return Response({'success': False, 'message': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    is_active = request.data.get('is_active')
    if is_active is None:
        # toggle if not provided
        dept.is_active = not dept.is_active
    else:
        is_active_bool = is_active if isinstance(is_active, bool) else str(is_active).lower() in ['1', 'true', 'yes']
        dept.is_active = is_active_bool
    dept.save(update_fields=['is_active'])
    return Response({'success': True, 'data': DepartmentSerializer(dept).data}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def create_employee(request):
    """
    Create a new employee profile
    Only HR managers and super admins can create employee profiles
    """
    try:
        serializer = EmployeeCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Split full name into first and last name
        full_name_parts = data['full_name'].strip().split(' ', 1)
        first_name = full_name_parts[0]
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''

        with transaction.atomic():
            # Create user account
            user = User.objects.create_user(
                username=data['email'],  # Use email as username
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                role='employee',
                company=request.user.company,
                created_by=request.user,
                is_active=True
            )

            # Set a default password (should be changed on first login)
            user.set_password('TempPass123!')
            user.save()

            # Get department
            department = Department.objects.get(id=data['department_id'], company=request.user.company)

            # Generate employee ID if not provided
            employee_id = data.get('employee_id')
            if not employee_id:
                # Generate auto employee ID
                last_employee = Employee.objects.filter(company=request.user.company).order_by('-id').first()
                next_id = (last_employee.id + 1) if last_employee else 1
                employee_id = f"EMP{next_id:04d}"

            # Create employee profile
            employee = Employee.objects.create(
                user=user,
                company=request.user.company,
                employee_id=employee_id,
                department=department,
                job_title=data['designation'],
                phone=data.get('phone', ''),
                salary=data.get('salary'),
                hire_date=timezone.now().date(),
                is_active=True
            )

            # Create default leave balance
            LeaveBalance.objects.create(
                employee=employee,
                annual_leave_total=20,
                annual_leave_used=0,
                sick_leave_total=10,
                sick_leave_used=0,
                personal_leave_total=5,
                personal_leave_used=0
            )

            logger.info(f"Employee created: {employee.employee_id} by {request.user.username}")

            return Response({
                'success': True,
                'message': 'Employee profile created successfully',
                'data': {
                    'employee_id': employee.employee_id,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'department': department.name,
                    'job_title': employee.job_title,
                    'default_password': 'TempPass123!'
                }
            }, status=status.HTTP_201_CREATED)

    except Department.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Department not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while creating the employee profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_role('super_admin')
def create_hr(request):
    """
    Create a new HR manager profile
    Only super admins can create HR manager profiles
    """
    try:
        serializer = HRCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Split full name into first and last name
        full_name_parts = data['full_name'].strip().split(' ', 1)
        first_name = full_name_parts[0]
        last_name = full_name_parts[1] if len(full_name_parts) > 1 else ''

        with transaction.atomic():
            # Create user account
            user = User.objects.create_user(
                username=data['email'],  # Use email as username
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                role='hr_manager',
                company=request.user.company,
                created_by=request.user,
                is_active=True
            )

            # Set a default password (should be changed on first login)
            user.set_password('TempPass123!')
            user.save()

            # Get department
            department = Department.objects.get(id=data['department_id'], company=request.user.company)

            # Generate employee ID if not provided
            employee_id = data.get('employee_id')
            if not employee_id:
                # Generate auto employee ID
                last_employee = Employee.objects.filter(company=request.user.company).order_by('-id').first()
                next_id = (last_employee.id + 1) if last_employee else 1
                employee_id = f"HR{next_id:04d}"

            # Create employee profile
            employee = Employee.objects.create(
                user=user,
                company=request.user.company,
                employee_id=employee_id,
                department=department,
                job_title=data['designation'],
                phone=data.get('phone', ''),
                salary=data.get('salary'),
                hire_date=timezone.now().date(),
                is_active=True
            )

            # Create default leave balance
            LeaveBalance.objects.create(
                employee=employee,
                annual_leave_total=25,  # HR gets more leave
                annual_leave_used=0,
                sick_leave_total=15,
                sick_leave_used=0,
                personal_leave_total=10,
                personal_leave_used=0
            )

            logger.info(f"HR Manager created: {employee.employee_id} by {request.user.username}")

            return Response({
                'success': True,
                'message': 'HR Manager profile created successfully',
                'data': {
                    'employee_id': employee.employee_id,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'department': department.name,
                    'job_title': employee.job_title,
                    'default_password': 'TempPass123!'
                }
            }, status=status.HTTP_201_CREATED)

    except Department.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Department not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating HR manager: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while creating the HR manager profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def list_employees(request):
    """
    List employees with search, filter and basic pagination.
    Query params:
      - q: search by name/email/employee_id/department
      - department_id: filter by department
      - status: active|inactive|all (default active)
      - hire_date_from, hire_date_to: YYYY-MM-DD
      - page (1-based), page_size
    """
    try:
        qs = Employee.objects.filter(
            company=request.user.company,
            user__role='employee',
        ).select_related('user', 'department').order_by('employee_id')

        status_param = (request.GET.get('status') or 'active').lower()
        if status_param == 'active':
            qs = qs.filter(is_active=True)
        elif status_param == 'inactive':
            qs = qs.filter(is_active=False)

        q = (request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(employee_id__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(department__name__icontains=q)
            )

        dept_id = request.GET.get('department_id')
        if dept_id:
            qs = qs.filter(department_id=dept_id)

        # Hire date range filters
        fmt = '%Y-%m-%d'
        hire_from = request.GET.get('hire_date_from')
        hire_to = request.GET.get('hire_date_to')
        try:
            if hire_from:
                qs = qs.filter(hire_date__gte=datetime.strptime(hire_from, fmt).date())
            if hire_to:
                qs = qs.filter(hire_date__lte=datetime.strptime(hire_to, fmt).date())
        except ValueError:
            pass

        total = qs.count()
        # Pagination
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page, page_size = 1, 25
        start = (page - 1) * page_size
        end = start + page_size

        serializer = EmployeeListSerializer(qs[start:end], many=True)
        return Response({
            'success': True,
            'message': 'Employees retrieved successfully',
            'data': serializer.data,
            'count': total,
            'page': page,
            'page_size': page_size
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error listing employees: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving employees'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_role('super_admin')
def list_hr(request):
    """
    List all HR manager profiles
    Only super admins can view HR manager lists
    """
    try:
        hr_managers = Employee.objects.filter(
            company=request.user.company,
            user__role='hr_manager',
            is_active=True
        ).select_related('user', 'department').order_by('employee_id')

        serializer = HRListSerializer(hr_managers, many=True)

        return Response({
            'success': True,
            'message': 'HR Managers retrieved successfully',
            'data': serializer.data,
            'count': hr_managers.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error listing HR managers: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving HR managers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def employee_detail(request, pk: int):
    """Return comprehensive employee details including leave and recent attendance."""
    try:
        employee = Employee.objects.select_related('user', 'department').get(
            id=pk, company=request.user.company
        )
        emp_data = EmployeeDetailSerializer(employee).data

        # Leave balance
        leave = None
        try:
            lb = employee.leavebalance
            leave = {
                'annual_total': lb.annual_leave_total,
                'annual_used': lb.annual_leave_used,
                'annual_remaining': lb.annual_leave_total - lb.annual_leave_used,
                'sick_total': lb.sick_leave_total,
                'sick_used': lb.sick_leave_used,
                'sick_remaining': lb.sick_leave_total - lb.sick_leave_used,
                'personal_total': lb.personal_leave_total,
                'personal_used': lb.personal_leave_used,
                'personal_remaining': lb.personal_leave_total - lb.personal_leave_used,
            }
        except Exception:
            leave = None

        # Recent attendance (last 10 records)
        recent_attendance = list(
            Attendance.objects.filter(employee=employee)
            .order_by('-date')
            .values('date', 'status', 'total_hours')[:10]
        )

        return Response({
            'success': True,
            'data': {
                'employee': emp_data,
                'leave_balance': leave,
                'recent_attendance': recent_attendance,
            }
        }, status=status.HTTP_200_OK)
    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching employee detail: {e}")
        return Response({'success': False, 'message': 'Unable to fetch employee details'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def update_employee(request, pk: int):
    """Update employee and related user fields."""
    try:
        employee = Employee.objects.select_related('user').get(id=pk, company=request.user.company)
    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeUpdateSerializer(data=request.data, context={'request': request, 'employee': employee})
    if not serializer.is_valid():
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        with transaction.atomic():
            user = employee.user
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data and data['email']:
                user.email = data['email']
                # Keep username aligned to email if your system uses that convention
                user.username = data['email']
            user.save()

            if 'phone' in data:
                employee.phone = data['phone']
            if 'address' in data:
                employee.address = data['address']
            if 'date_of_birth' in data:
                employee.date_of_birth = data['date_of_birth']
            if 'job_title' in data:
                employee.job_title = data['job_title']
            if 'salary' in data:
                employee.salary = data['salary']
            if 'department_id' in data and data['department_id'] is not None:
                employee.department = Department.objects.get(id=data['department_id'], company=request.user.company)
            if 'is_active' in data:
                employee.is_active = data['is_active']
                # Keep User active flag in sync to control login access
                user.is_active = data['is_active']
                user.save(update_fields=['is_active'])
            employee.save()

        return Response({'success': True, 'message': 'Employee updated successfully'}, status=status.HTTP_200_OK)
    except Department.DoesNotExist:
        return Response({'success': False, 'message': 'Invalid department'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        return Response({'success': False, 'message': 'Unable to update employee'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def change_employee_status(request, pk: int):
    """Soft-activate/deactivate an employee and corresponding user."""
    try:
        employee = Employee.objects.select_related('user').get(id=pk, company=request.user.company)
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'success': False, 'message': 'is_active is required'}, status=status.HTTP_400_BAD_REQUEST)
        is_active = bool(is_active) if isinstance(is_active, bool) else str(is_active).lower() in ['1', 'true', 'yes']
        employee.is_active = is_active
        employee.user.is_active = is_active
        with transaction.atomic():
            employee.user.save(update_fields=['is_active'])
            employee.save(update_fields=['is_active'])
        return Response({'success': True, 'message': 'Status updated', 'is_active': is_active}, status=status.HTTP_200_OK)
    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error changing status: {e}")
        return Response({'success': False, 'message': 'Unable to change status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def bulk_update_employees(request):
    """Bulk actions: transfer_department, set_status."""
    action = request.data.get('action')
    ids = request.data.get('ids') or []
    if not action or not isinstance(ids, list) or not ids:
        return Response({'success': False, 'message': 'action and ids are required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        employees = Employee.objects.filter(id__in=ids, company=request.user.company).select_related('user')
        updated = 0
        if action == 'transfer_department':
            dept_id = request.data.get('department_id')
            if not dept_id:
                return Response({'success': False, 'message': 'department_id required'}, status=status.HTTP_400_BAD_REQUEST)
            dept = Department.objects.get(id=dept_id, company=request.user.company)
            updated = employees.update(department=dept)
        elif action == 'set_status':
            is_active = request.data.get('is_active')
            if is_active is None:
                return Response({'success': False, 'message': 'is_active required'}, status=status.HTTP_400_BAD_REQUEST)
            is_active = bool(is_active) if isinstance(is_active, bool) else str(is_active).lower() in ['1', 'true', 'yes']
            for emp in employees:
                emp.is_active = is_active
                emp.user.is_active = is_active
                emp.user.save(update_fields=['is_active'])
                emp.save(update_fields=['is_active'])
                updated += 1
        else:
            return Response({'success': False, 'message': 'Unsupported action'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'updated': updated}, status=status.HTTP_200_OK)
    except Department.DoesNotExist:
        return Response({'success': False, 'message': 'Invalid department'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error bulk updating employees: {e}")
        return Response({'success': False, 'message': 'Bulk action failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def export_employees(request):
    """Export employees as CSV using same filters as list_employees."""
    try:
        # Reuse list filters
        response_list = list_employees(request)
        if response_list.status_code != 200:
            return response_list
        data = response_list.data.get('data', [])

        # Build CSV
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="employees.csv"'
        writer = csv.writer(resp)
        writer.writerow(['Employee ID', 'Full Name', 'Email', 'Department', 'Job Title', 'Phone', 'Hire Date', 'Status'])
        for e in data:
            writer.writerow([
                e.get('employee_id'),
                e.get('full_name'),
                e.get('email'),
                e.get('department_name'),
                e.get('job_title'),
                e.get('phone'),
                e.get('hire_date'),
                'Active' if e.get('is_active') else 'Inactive'
            ])
        return resp
    except Exception as e:
        logger.error(f"Error exporting employees: {e}")
        return Response({'success': False, 'message': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Biometric Integration APIs (ZKTeco-compatible) ---

def _hmac_valid(secret: str, body: bytes, signature: str) -> bool:
    try:
        mac = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, (signature or '').lower())
    except Exception:
        return False


def _get_device_by_key(api_key: str):
    try:
        return BiometricDevice.objects.get(api_key=api_key, is_active=True)
    except BiometricDevice.DoesNotExist:
        return None


def _parse_event_timestamp(ts_value, fallback_tz='UTC'):
    # Accept ISO8601 string or epoch seconds
    if ts_value is None:
        return None
    if isinstance(ts_value, (int, float)):
        dt = datetime.utcfromtimestamp(float(ts_value))
        return timezone.make_aware(dt, timezone.utc)
    if isinstance(ts_value, str):
        dt = parse_datetime(ts_value)
        if dt is None:
            # try as epoch string
            try:
                dt = datetime.utcfromtimestamp(float(ts_value))
                return timezone.make_aware(dt, timezone.utc)
            except Exception:
                return None
        if timezone.is_naive(dt):
            # assume provided in fallback tz, convert to UTC
            try:
                return timezone.make_aware(dt)
            except Exception:
                return timezone.make_aware(dt, timezone.utc)
        return dt
    return None


def _recompute_attendance(att):
    ci, co = att.clock_in, att.clock_out
    if ci and co:
        # both are time objects; compute delta assuming same date and handle overnight
        in_dt = datetime.combine(att.date, ci)
        out_dt = datetime.combine(att.date, co)
        if out_dt < in_dt:
            out_dt += timedelta(days=1)
        delta = out_dt - in_dt
        if att.break_duration:
            delta -= att.break_duration
        hours = Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.01'))
        att.total_hours = hours
    return att


def _process_event(company, device, device_user_id, event_type, ts, raw_payload=None):
    # Idempotency key
    base = f"{device.id if device else 'N'}|{company.id}|{device_user_id}|{int(ts.timestamp())}|{event_type}"
    dedupe = hashlib.sha256(base.encode('utf-8')).hexdigest()
    ev, created = BiometricEvent.objects.get_or_create(
        dedupe_hash=dedupe,
        defaults={
            'company': company,
            'device': device,
            'device_user_id': str(device_user_id),
            'event_type': event_type if event_type in ['checkin','checkout'] else 'unknown',
            'timestamp': ts,
            'raw_payload': raw_payload or {},
            'processed': False,
        }
    )
    if not created:
        return ev, False  # duplicate

    # Try to map to Employee
    emp = None
    if device:
        mapping = BiometricUserMap.objects.filter(company=company, device=device, device_user_id=str(device_user_id)).select_related('employee').first()
        if mapping:
            emp = mapping.employee
    if emp is None:
        # Fallback: try a global mapping
        mapping = BiometricUserMap.objects.filter(company=company, global_user_id=str(device_user_id)).select_related('employee').first()
        if mapping:
            emp = mapping.employee
    if emp is None:
        # Fallback: try employee_id match
        emp = Employee.objects.filter(company=company, employee_id=str(device_user_id)).first()

    if emp is None:
        # leave unprocessed to be resolved later
        return ev, True

    # Upsert Attendance by local date of device/company
    local_dt = ts.astimezone(timezone.get_current_timezone())
    att_date = local_dt.date()
    att, _ = Attendance.objects.get_or_create(employee=emp, date=att_date, defaults={'status': 'present'})
    t = local_dt.time()
    if event_type == 'checkin':
        if not att.clock_in or t < att.clock_in:
            att.clock_in = t
    elif event_type == 'checkout':
        if not att.clock_out or t > att.clock_out:
            att.clock_out = t
    att.status = att.status or 'present'
    att = _recompute_attendance(att)
    att.save()

    ev.processed = True
    ev.attendance = att
    ev.save(update_fields=['processed', 'attendance'])
    return ev, True


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def ingest_biometric_event(request):
    """Public endpoint for device/cloud to push real-time punches.
    Security: require X-Device-Key header. Optional HMAC in X-Signature (hex of SHA256 over raw body using api_key).
    Payload example:
    {"device_user_id":"23","event_type":"checkin","timestamp":"2025-09-17T09:05:23Z","external_event_id":"abc","payload":{...}}
    """
    try:
        api_key = request.headers.get('X-Device-Key') or request.GET.get('key')
        if not api_key:
            return Response({'success': False, 'message': 'Missing device key'}, status=401)
        device = _get_device_by_key(api_key)
        if not device or not device.is_active:
            return Response({'success': False, 'message': 'Invalid or inactive device'}, status=401)

        sig = request.headers.get('X-Signature')
        if sig and not _hmac_valid(device.api_key, request.body, sig):
            return Response({'success': False, 'message': 'Invalid signature'}, status=401)

        data = request.data if isinstance(request.data, dict) else json.loads(request.body.decode('utf-8') or '{}')
        device_user_id = data.get('device_user_id') or data.get('user_id') or data.get('pin')
        event_type = (data.get('event_type') or '').lower()
        ts = _parse_event_timestamp(data.get('timestamp'))
        if not device_user_id or not ts or event_type not in ['checkin','checkout']:
            return Response({'success': False, 'message': 'device_user_id, timestamp and valid event_type are required'}, status=400)

        ev, ok = _process_event(device.company, device, str(device_user_id), event_type, ts, raw_payload=data)
        device.last_seen = timezone.now()
        device.save(update_fields=['last_seen'])
        status_text = 'accepted' if ok else 'duplicate'
        return Response({'success': True, 'status': status_text, 'event_id': ev.id, 'processed': ev.processed}, status=200)
    except Exception as e:
        logger.exception('Error ingesting biometric event')
        return Response({'success': False, 'message': 'Server error'}, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def biometric_heartbeat(request):
    """Device heartbeat to update last_seen. Auth via X-Device-Key."""
    api_key = request.headers.get('X-Device-Key') or request.GET.get('key')
    if not api_key:
        return Response({'success': False, 'message': 'Missing device key'}, status=401)
    device = _get_device_by_key(api_key)
    if not device:
        return Response({'success': False, 'message': 'Invalid device'}, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def list_biometric_devices(request):
    qs = BiometricDevice.objects.filter(company=request.user.company).order_by('name')
    data = [{
        'id': d.id,
        'name': d.name,
        'brand': d.brand,
        'model': d.model,
        'serial_number': d.serial_number,
        'ip_address': d.ip_address,
        'port': d.port,
        'push_enabled': d.push_enabled,
        'is_active': d.is_active,
        'last_seen': d.last_seen,
        'last_pull': d.last_pull,
    } for d in qs]
    return Response({'success': True, 'data': data}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def register_biometric_device(request):
    name = (request.data.get('name') or '').strip()
    if not name:
        return Response({'success': False, 'message': 'Name is required'}, status=400)
    device = BiometricDevice(
        company=request.user.company,
        name=name,
        brand=(request.data.get('brand') or 'ZKTeco')[:50],
        model=request.data.get('model') or '',
        serial_number=request.data.get('serial_number') or '',
        ip_address=request.data.get('ip_address') or None,
        port=int(request.data.get('port') or 4370),
        push_enabled=bool(request.data.get('push_enabled')) if request.data.get('push_enabled') is not None else True,
        is_active=True,
    )
    api_key = request.data.get('api_key') or secrets.token_hex(32)
    device.api_key = api_key
    device.save()
    return Response({'success': True, 'data': {'id': device.id, 'api_key': api_key}}, status=201)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def update_biometric_device(request, pk):
    try:
        d = BiometricDevice.objects.get(pk=pk, company=request.user.company)
    except BiometricDevice.DoesNotExist:
        return Response({'success': False, 'message': 'Device not found'}, status=404)

    # Validate and apply fields
    errors = {}
    data = request.data

    # Simple validators
    def _to_bool(val):
        return val if isinstance(val, bool) else str(val).lower() in ['1','true','yes','on']

    # Name/brand/model/serial/cloud/timezone
    for field in ['name','brand','model','serial_number','cloud_endpoint_url','timezone']:
        if field in data:
            setattr(d, field, (data.get(field) or '').strip())

    # IP validation
    if 'ip_address' in data:
        ip_val = (data.get('ip_address') or '').strip()
        if ip_val:
            try:
                import ipaddress
                ipaddress.ip_address(ip_val)
                d.ip_address = ip_val
            except Exception:
                errors['ip_address'] = 'Invalid IP address format'
        else:
            d.ip_address = None

    # Port validation
    if 'port' in data:
        try:
            p = int(data.get('port'))
            if p < 1 or p > 65535:
                errors['port'] = 'Port must be between 1 and 65535'
            else:
                d.port = p
        except Exception:
            errors['port'] = 'Port must be an integer'

    # COM key validation (0..999999)
    if 'comm_key' in data:
        v = str(data.get('comm_key')).strip()
        if v != '':
            try:
                ck = int(v)
                if ck < 0 or ck > 999999:
                    errors['comm_key'] = 'COM key must be 0..999999'
                else:
                    d.comm_key = ck
            except Exception:
                errors['comm_key'] = 'COM key must be a number'

    # Flags
    if 'push_enabled' in data:
        d.push_enabled = _to_bool(data.get('push_enabled'))
    if 'is_active' in data:
        d.is_active = _to_bool(data.get('is_active'))

    # API key updates (optional)
    if data.get('api_key'):
        d.api_key = str(data.get('api_key')).strip()
    if 'webhook_secret' in data:
        d.webhook_secret = str(data.get('webhook_secret') or '').strip()

    if errors:
        return Response({'success': False, 'errors': errors, 'message': 'Validation failed'}, status=400)

    d.save()
    return Response({'success': True, 'message': 'Device updated'}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def upsert_biometric_mapping(request):
    employee_id = request.data.get('employee_id')
    device_id = request.data.get('device_id')
    device_user_id = request.data.get('device_user_id')
    global_user_id = request.data.get('global_user_id')
    if not employee_id or not (device_user_id or global_user_id):
        return Response({'success': False, 'message': 'employee_id and device_user_id or global_user_id required'}, status=400)
    try:
        emp = Employee.objects.get(pk=employee_id, company=request.user.company)
    except Employee.DoesNotExist:
        return Response({'success': False, 'message': 'Employee not found'}, status=404)
    device = None
    if device_id:
        try:
            device = BiometricDevice.objects.get(pk=device_id, company=request.user.company)
        except BiometricDevice.DoesNotExist:
            return Response({'success': False, 'message': 'Device not found'}, status=404)
    if device and device_user_id:
        obj, _ = BiometricUserMap.objects.update_or_create(
            company=request.user.company, device=device, device_user_id=str(device_user_id),
            defaults={'employee': emp}
        )
    elif global_user_id:
        obj, _ = BiometricUserMap.objects.update_or_create(
            company=request.user.company, device=None, device_user_id=str(global_user_id),
            defaults={'employee': emp, 'global_user_id': str(global_user_id)}
        )
    else:
        return Response({'success': False, 'message': 'Invalid mapping payload'}, status=400)
    return Response({'success': True, 'mapping_id': obj.id}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def biometric_status(request):
    company = request.user.company
    since = timezone.now() - timedelta(days=1)
    devices = BiometricDevice.objects.filter(company=company)
    device_stats = []
    for d in devices:
        device_stats.append({
            'id': d.id,
            'name': d.name,
            'last_seen': d.last_seen,
            'last_pull': d.last_pull,
            'is_active': d.is_active,
            'push_enabled': d.push_enabled,
        })
    processed_count = BiometricEvent.objects.filter(company=company, processed=True, timestamp__gte=since).count()
    pending_count = BiometricEvent.objects.filter(company=company, processed=False, timestamp__gte=since).count()
    return Response({'success': True, 'devices': device_stats, 'events': {'processed_24h': processed_count, 'pending_24h': pending_count}}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def list_recent_biometric_events(request):
    """List recent biometric events for the current company with optional filters.
    Params: hours (int, default 48), device_id (int), event_type (checkin|checkout|unknown)
    """
    hours = int(request.GET.get('hours') or 48)
    since = timezone.now() - timedelta(hours=hours)
    qs = BiometricEvent.objects.filter(company=request.user.company, timestamp__gte=since)
    device_id = request.GET.get('device_id')
    if device_id:
        qs = qs.filter(device_id=device_id)
    event_type = (request.GET.get('event_type') or '').lower()
    if event_type in ['checkin', 'checkout', 'unknown']:
        qs = qs.filter(event_type=event_type)
    qs = qs.select_related('device', 'attendance').order_by('-timestamp')[:500]
    data = [{
        'id': ev.id,
        'device': ev.device.name if ev.device else None,
        'device_id': ev.device_id,
        'device_user_id': ev.device_user_id,
        'event_type': ev.event_type,
        'timestamp': ev.timestamp,
        'processed': ev.processed,
    } for ev in qs]
    return Response({'success': True, 'data': data}, status=200)

    pending_count = BiometricEvent.objects.filter(company=company, processed=False, timestamp__gte=since).count()
    return Response({'success': True, 'devices': device_stats, 'events': {'processed_24h': processed_count, 'pending_24h': pending_count}}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def biometric_attendance_list(request):
    """List biometric attendance records."""
    events = BiometricEvent.objects.filter(company=request.user.company).select_related('device', 'attendance').order_by('-timestamp')[:500]
    serializer = BiometricEventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def biometric_attendance_edit(request, pk):
    """Edit a biometric attendance record."""
    try:
        event = BiometricEvent.objects.get(pk=pk, company=request.user.company)
    except BiometricEvent.DoesNotExist:
        return Response({'error': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = BiometricEventSerializer(event, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def biometric_attendance_bulk_edit(request):
    """Bulk edit biometric attendance records."""
    serializer = BiometricEventBulkEditSerializer(data=request.data)
    if serializer.is_valid():
        ids = serializer.validated_data['ids']
        updates = {k: v for k, v in serializer.validated_data.items() if k != 'ids'}
        updated = []
        for eid in ids:
            try:
                event = BiometricEvent.objects.get(pk=eid, company=request.user.company)
                for attr, value in updates.items():
                    setattr(event, attr, value)
                event.save()
                updated.append(event.id)
            except BiometricEvent.DoesNotExist:
                continue
        return Response({'updated': updated})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def biometric_user_map_correction(request, pk):
    """Correct mismatched employee mapping for device_user_id."""
    try:
        mapping = BiometricUserMap.objects.get(pk=pk, company=request.user.company)
    except BiometricUserMap.DoesNotExist:
        return Response({'error': 'Mapping not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = BiometricUserMapCorrectionSerializer(mapping, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(["DELETE", "POST"])
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def delete_biometric_device(request, pk):
    """Delete a biometric device. Cascades BiometricUserMap; BiometricEvent.device set NULL.
    Handles edge cases for active connections by blocking unless force=true.
    """
    try:
        d = BiometricDevice.objects.get(pk=pk, company=request.user.company)
    except BiometricDevice.DoesNotExist:
        return Response({'success': False, 'message': 'Device not found'}, status=404)

    force = str(request.data.get('force') if request.method == 'POST' else request.GET.get('force', '')).lower() in ['1','true','yes']
    # If device appears to be in use (recent last_seen within 15s), block unless force=true
    if d.last_seen and (timezone.now() - d.last_seen).total_seconds() < 15 and not force:
        return Response({'success': False, 'message': 'Device appears to be in use. Stop live listener or retry later. Pass force=true to override.'}, status=409)

    name = d.name
    # Deleting BiometricDevice will CASCADE BiometricUserMap, and BiometricEvent FK is SET_NULL per model
    d.delete()
    return Response({'success': True, 'message': f'Device "{name}" deleted'}, status=200)


@api_view(["GET"])  # simple connectivity check
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def ping_biometric_device(request, pk):
    try:
        d = BiometricDevice.objects.get(pk=pk, company=request.user.company)
    except BiometricDevice.DoesNotExist:
        return Response({'success': False, 'message': 'Device not found'}, status=404)

    if not d.ip_address or not d.port:
        return Response({'success': True, 'connected': False, 'message': 'IP/port not configured'}, status=200)
    if not d.is_active:
        return Response({'success': True, 'connected': False, 'message': 'Device inactive'}, status=200)

    try:
        from zk import ZK
        from zk.exception import ZKNetworkError
    except Exception:
        return Response({'success': False, 'connected': False, 'message': 'python-zk not installed'}, status=500)

    start = time.time()
    try:
        password = int(getattr(d, 'comm_key', 0) or 0)
        try:
            zk = ZK(d.ip_address, port=d.port, timeout=5, password=password, force_udp=False, ommit_ping=False)
            conn = zk.connect()
        except Exception:
            # Fallback to UDP transport
            zk = ZK(d.ip_address, port=d.port, timeout=5, password=password, force_udp=True, ommit_ping=False)
            conn = zk.connect()
        try:
            # A light command to verify responsiveness
            try:
                conn.disable_device()
                conn.enable_device()
            except Exception:
                pass
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass
        latency = int((time.time() - start) * 1000)
        # update last_seen
        d.last_seen = timezone.now()
        d.save(update_fields=['last_seen'])
        return Response({'success': True, 'connected': True, 'latency_ms': latency, 'last_seen': d.last_seen}, status=200)
    except Exception as e:
        msg = str(e)
        return Response({'success': True, 'connected': False, 'message': msg}, status=200)


@api_view(["POST"])  # server-side sync of all attendance logs
@permission_classes([IsAuthenticated])
@require_roles('hr_manager', 'super_admin')
def sync_biometric_device(request, pk):
    """Connect to the device and import attendance logs. Optionally limit via since_minutes param."""
    try:
        d = BiometricDevice.objects.get(pk=pk, company=request.user.company)
    except BiometricDevice.DoesNotExist:
        return Response({'success': False, 'message': 'Device not found'}, status=404)

    since_minutes = int(request.data.get('since_minutes') or 0)
    try:
        from zk import ZK
    except Exception:
        return Response({'success': False, 'message': 'python-zk not installed'}, status=500)

    ingested = duplicates = errors = 0
    try:
        password = int(getattr(d, 'comm_key', 0) or 0)
        try:
            zk = ZK(d.ip_address, port=d.port, timeout=10, password=password, force_udp=False, ommit_ping=False)
            conn = zk.connect()
        except Exception:
            zk = ZK(d.ip_address, port=d.port, timeout=10, password=password, force_udp=True, ommit_ping=False)
            conn = zk.connect()
        try:
            records = conn.get_attendance() or []
            now = timezone.now()
            cutoff = now - timedelta(minutes=since_minutes) if since_minutes else None
            for r in records:
                try:
                    ts = getattr(r, 'timestamp', None)
                    if ts and ts.tzinfo is None:
                        ts = timezone.make_aware(ts)
                    if cutoff and ts and ts < cutoff:
                        continue
                    punch = getattr(r, 'punch', getattr(r, 'status', 0))
                    event_type = 'checkin' if punch in (0, 4) else 'checkout'
                    ev, created = _process_event(d.company, d, str(getattr(r, 'user_id', '')), event_type, ts, raw_payload={'source': 'sync', 'raw': str(r)})
                    if created:
                        ingested += 1
                    else:
                        duplicates += 1
                except Exception:
                    errors += 1
            d.last_pull = timezone.now()
            d.save(update_fields=['last_pull'])
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass
        return Response({'success': True, 'ingested': ingested, 'duplicates': duplicates, 'errors': errors, 'last_pull': d.last_pull}, status=200)
    except Exception as e:
        logger.exception('Sync failed for device %s', pk)
        return Response({'success': False, 'message': str(e)}, status=500)


