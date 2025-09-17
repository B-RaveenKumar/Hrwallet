from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.decorators import require_role, require_roles
from core_hr.models import Employee, Department, LeaveBalance, Attendance
from .serializers import (
    EmployeeCreateSerializer, HRCreateSerializer,
    EmployeeListSerializer, HRListSerializer, DepartmentSerializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

from django.db.models import Q
from django.http import HttpResponse
import csv
from datetime import datetime


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

