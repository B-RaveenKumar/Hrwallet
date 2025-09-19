from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .decorators import audit_action
from .models import User
from core_hr.models import Company, Department, Employee, LeaveBalance
import logging
import json

logger = logging.getLogger(__name__)


@csrf_protect
@never_cache
def company_selection_view(request):
    """
    Company selection page - first step in authentication flow
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    # Handle POST request - company selection
    if request.method == 'POST':
        company_id = request.POST.get('company_id')

        if not company_id:
            messages.error(request, 'Please select a company to continue.')
        else:
            try:
                # Validate company exists and is active
                company = Company.objects.get(id=company_id, is_active=True)

                # Store selected company in session
                request.session['selected_company_id'] = company.id
                request.session['selected_company_name'] = company.name

                # Redirect to login page
                return redirect('accounts:login')

            except Company.DoesNotExist:
                messages.error(request, 'Invalid company selection. Please try again.')
            except Exception as e:
                logger.error(f"Error in company selection: {str(e)}")
                messages.error(request, 'An error occurred. Please try again.')

    # Handle GET request - show company selection form
    try:
        # Get all active companies
        companies = Company.objects.filter(is_active=True).order_by('name')

        # Add employee count to each company
        for company in companies:
            try:
                company.employee_count = company.employees.filter(is_active=True).count()
            except Exception:
                company.employee_count = 0

        context = {
            'page_title': 'Select Your Company',
            'companies': companies,
        }

        return render(request, 'accounts/company_selection.html', context)

    except Exception as e:
        logger.error(f"Error loading companies: {str(e)}")
        messages.error(request, 'Unable to load companies. Please contact support.')

        # Fallback - redirect to login with default company
        return redirect('accounts:login')


@csrf_protect
@never_cache
@audit_action('login_attempt')
def login_view(request):
    """
    Login view with company context from session
    """
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    # Check if company was selected in session
    selected_company_id = request.session.get('selected_company_id')
    selected_company_name = request.session.get('selected_company_name')

    # If no company selected, redirect to company selection
    if not selected_company_id:
        return redirect('accounts:company_selection')

    # Get the selected company
    selected_company = None
    try:
        selected_company = Company.objects.get(id=selected_company_id, is_active=True)
    except Company.DoesNotExist:
        # Company no longer exists or is inactive, clear session and redirect
        request.session.pop('selected_company_id', None)
        request.session.pop('selected_company_name', None)
        messages.error(request, 'Selected company is no longer available. Please select again.')
        return redirect('accounts:company_selection')
    except Exception as e:
        logger.error(f"Error accessing selected company: {str(e)}")
        return redirect('accounts:company_selection')

    if request.method == 'POST':
        username_input = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if username_input and password:
            user = None

            # 1) Try direct username (supports existing username or email-as-username)
            user = authenticate(request, username=username_input, password=password)

            # 2) Try by email (if the identifier is an email stored in User.email)
            if user is None:
                try:
                    lookup_user = User.objects.filter(email=username_input).first()
                    if lookup_user:
                        user = authenticate(request, username=lookup_user.username, password=password)
                except Exception:
                    pass

            # 3) Try by employee_id (EMP0001/HR0001 style) - only within selected company
            if user is None:
                try:
                    emp = Employee.objects.filter(
                        employee_id=username_input,
                        company=selected_company
                    ).select_related('user').first()
                    if emp and emp.user:
                        user = authenticate(request, username=emp.user.username, password=password)
                except Exception:
                    pass

            if user is not None:
                if user.is_active:
                    # Verify user belongs to selected company (for employees)
                    user_company_valid = True
                    if hasattr(user, 'employee'):
                        try:
                            if user.employee.company != selected_company:
                                user_company_valid = False
                                messages.error(request, f'Your account is not associated with {selected_company.name}.')
                        except Exception:
                            pass

                    # For non-employee users (super_admin), assign selected company
                    if user_company_valid:
                        if hasattr(user, 'company') and not user.company:
                            try:
                                user.company = selected_company
                                user.save()
                            except Exception as e:
                                logger.warning(f"Could not assign company to user {username_input}: {str(e)}")

                        login(request, user)

                        # Clear company selection from session after successful login
                        request.session.pop('selected_company_id', None)
                        request.session.pop('selected_company_name', None)

                        # Get role safely
                        role = getattr(user, 'role', 'employee')
                        logger.info(f"Successful login: {user.username} (role: {role}) at {selected_company.name}")

                        # Redirect to appropriate dashboard based on role
                        next_url = request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        else:
                            # Dashboard redirect based on role
                            if role == 'super_admin':
                                return redirect('/admin-panel/')
                            elif role == 'hr_manager':
                                return redirect('/hr-dashboard/')
                            else:
                                return redirect('/employee-portal/')
                else:
                    messages.error(request, 'Your account is disabled.')
                    logger.warning(f"Login attempt with disabled account: {username_input}")
            else:
                messages.error(request, 'Invalid username/email/employee ID or password.')
                logger.warning(f"Failed login attempt: {username_input}")
        else:
            messages.error(request, 'Please provide both username and password.')

    context = {
        'page_title': f'Login to {selected_company_name}',
        'selected_company': selected_company,
        'selected_company_name': selected_company_name,
    }

    return render(request, 'accounts/login.html', context)


@login_required
@audit_action('logout')
def logout_view(request):
    """
    Custom logout view - redirects directly to login
    """
    username = request.user.username
    logout(request)
    logger.info(f"User logged out: {username}")
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


@login_required
@audit_action('dashboard_access')
def dashboard_view(request):
    """
    Main dashboard that redirects to role-specific dashboard
    """
    return redirect(request.user.get_dashboard_url())


@login_required
def profile_view(request):
    """
    User profile view
    """
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


# Real-Time User Management API Views

@login_required
@require_http_methods(["GET", "POST"])
def create_user_api(request):
    """
    AJAX API for creating new users in real-time
    """
    if request.user.role not in ['super_admin', 'hr_manager']:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['username', 'email', 'first_name', 'last_name', 'role']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'{field} is required'}, status=400)

            # Check if username already exists
            from .models import User
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            # Check if email already exists
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    password=data.get('password', 'temp123'),  # Default password
                    role=data['role'],
                    company=request.user.company,
                    created_by=request.user
                )

                # Auto-create an Employee profile for employee/hr_manager roles
                employee_id_value = None
                if user.role in ['employee', 'hr_manager']:
                    prefix = 'HR' if user.role == 'hr_manager' else 'EMP'
                    last_employee = Employee.objects.filter(company=request.user.company).order_by('-id').first()
                    next_id = (last_employee.id + 1) if last_employee else 1
                    generated_employee_id = f"{prefix}{next_id:04d}"

                    # Optional fields from payload (best-effort)
                    job_title = data.get('job_title') or ('HR Manager' if user.role == 'hr_manager' else 'Staff')
                    phone = data.get('phone') or ''
                    salary = data.get('salary')  # may be None

                    department = None
                    dept_id = data.get('department_id')
                    if isinstance(dept_id, int):
                        try:
                            department = Department.objects.get(id=dept_id, company=request.user.company)
                        except Department.DoesNotExist:
                            department = None

                    employee = Employee.objects.create(
                        user=user,
                        company=request.user.company,
                        employee_id=generated_employee_id,
                        department=department,
                        job_title=job_title,
                        phone=phone,
                        salary=salary,
                        hire_date=timezone.now().date(),
                        is_active=True
                    )

                    # Create default leave balance aligned with profile_api
                    if user.role == 'hr_manager':
                        LeaveBalance.objects.create(
                            employee=employee,
                            annual_leave_total=25,
                            annual_leave_used=0,
                            sick_leave_total=15,
                            sick_leave_used=0,
                            personal_leave_total=10,
                            personal_leave_used=0
                        )
                    else:
                        LeaveBalance.objects.create(
                            employee=employee,
                            annual_leave_total=20,
                            annual_leave_used=0,
                            sick_leave_total=10,
                            sick_leave_used=0,
                            personal_leave_total=5,
                            personal_leave_used=0
                        )

                    employee_id_value = employee.employee_id

                logger.info(f"User created: {user.username} by {request.user.username}")

                return JsonResponse({
                    'success': True,
                    'message': 'User created successfully',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.get_full_name(),
                        'role': user.get_role_display(),
                        'is_active': user.is_active,
                        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M')
                    },
                    'employee_id': employee_id_value
                })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return JsonResponse({'error': 'Failed to create user'}, status=500)

    # GET request - return form data with error handling
    try:
        companies = Company.objects.all().order_by('name')
        from .models import User
        return JsonResponse({
            'companies': [{'id': c.id, 'name': c.name} for c in companies],
            'roles': [{'value': role[0], 'label': role[1]} for role in User.ROLE_CHOICES]
        })
    except Exception as e:
        return JsonResponse({
            'companies': [],
            'roles': [],
            'error': 'Unable to load form data'
        })

# -----------------------------
# Admin User Management APIs
# -----------------------------

def _ensure_admin(request):
    if request.user.role != 'super_admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    return None


def _serialize_user(user):
    emp = getattr(user, 'employee', None)
    dept = getattr(emp, 'department', None) if emp else None
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'role': user.role,
        'is_active': user.is_active,
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
        'employee': {
            'employee_id': getattr(emp, 'employee_id', None),
            'job_title': getattr(emp, 'job_title', None),
            'department': {
                'id': getattr(dept, 'id', None),
                'name': getattr(dept, 'name', None),
            } if dept else None,
        } if emp else None,
    }


@login_required
@require_http_methods(["GET"])
def list_users_api(request):
    deny = _ensure_admin(request)
    if deny:
        return deny

    qs = User.objects.filter(company=request.user.company).select_related('company').prefetch_related('employee__department')

    q = (request.GET.get('q') or '').strip()
    role = (request.GET.get('role') or '').strip()
    status = (request.GET.get('status') or '').strip()  # 'active' | 'inactive' | ''
    dept_id = request.GET.get('department_id')

    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(employee__employee_id__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if dept_id and dept_id.isdigit():
        qs = qs.filter(employee__department_id=int(dept_id))

    qs = qs.order_by('-date_joined')

    try:
        page = int(request.GET.get('page', '1'))
        page_size = int(request.GET.get('page_size', '20'))
    except ValueError:
        page, page_size = 1, 20

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = [_serialize_user(u) for u in qs[start:end]]

    return JsonResponse({'items': items, 'total': total, 'page': page, 'page_size': page_size})


@login_required
@require_http_methods(["GET"])
def user_detail_api(request, pk):
    deny = _ensure_admin(request)
    if deny:
        return deny

    user = get_object_or_404(User.objects.select_related('company').prefetch_related('employee__department'), pk=pk, company=request.user.company)
    return JsonResponse({'user': _serialize_user(user)})


@login_required
@require_http_methods(["PATCH"])
def update_user_api(request, pk):
    deny = _ensure_admin(request)
    if deny:
        return deny

    user = get_object_or_404(User, pk=pk, company=request.user.company)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    allowed_user_fields = ['first_name', 'last_name', 'email', 'role']

    with transaction.atomic():
        for f in allowed_user_fields:
            if f in data and data.get(f) is not None:
                setattr(user, f, data.get(f))
        user.save()

        # Update employee profile fields if exists
        try:
            emp = user.employee
        except Employee.DoesNotExist:
            emp = None
        if emp:
            if 'department_id' in data and data.get('department_id'):
                try:
                    dept = Department.objects.get(id=int(data['department_id']), company=request.user.company)
                    emp.department = dept
                except (Department.DoesNotExist, ValueError):
                    pass
            for f in ['job_title', 'phone', 'salary']:
                if f in data:
                    setattr(emp, f, data.get(f))
            emp.save()

    return JsonResponse({'success': True, 'user': _serialize_user(User.objects.select_related('company').prefetch_related('employee__department').get(pk=user.pk))})


@login_required
@require_http_methods(["PATCH"])
def change_user_status_api(request, pk):
    deny = _ensure_admin(request)
    if deny:
        return deny

    user = get_object_or_404(User, pk=pk, company=request.user.company)
    try:
        data = json.loads(request.body or '{}')
        is_active = bool(data.get('is_active'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    with transaction.atomic():
        user.is_active = is_active
        user.save()
        try:
            emp = user.employee
            emp.is_active = is_active
            emp.save()
        except Employee.DoesNotExist:
            pass

    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def bulk_update_users_api(request):
    deny = _ensure_admin(request)
    if deny:
        return deny

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    ids = data.get('ids') or []
    action = data.get('action')
    if not isinstance(ids, list) or not action:
        return JsonResponse({'error': 'ids (list) and action are required'}, status=400)

    users = User.objects.filter(company=request.user.company, id__in=ids)
    updated = 0

    with transaction.atomic():
        if action == 'set_status':
            is_active = bool(data.get('is_active'))
            updated = users.update(is_active=is_active)
            # Mirror to employees
            Employee.objects.filter(user__in=users).update(is_active=is_active)
        elif action == 'set_role':
            role = data.get('role')
            if role not in dict(User.ROLE_CHOICES):
                return JsonResponse({'error': 'Invalid role'}, status=400)
            for u in users:
                u.role = role
                u.save()
                updated += 1
        elif action == 'transfer_department':
            dept_id = data.get('department_id')
            try:
                dept = Department.objects.get(id=int(dept_id), company=request.user.company)
            except (Department.DoesNotExist, ValueError, TypeError):
                return JsonResponse({'error': 'Invalid department'}, status=400)
            emps = Employee.objects.filter(user__in=users)
            updated = emps.update(department=dept)
        else:
            return JsonResponse({'error': 'Unsupported action'}, status=400)

    return JsonResponse({'success': True, 'updated': updated})


@login_required
@require_http_methods(["GET"])
def export_users_api(request):
    deny = _ensure_admin(request)
    if deny:
        return deny

    # Reuse filters from list_users_api
    qs = User.objects.filter(company=request.user.company).select_related('company').prefetch_related('employee__department')
    q = (request.GET.get('q') or '').strip()
    role = (request.GET.get('role') or '').strip()
    status = (request.GET.get('status') or '').strip()
    dept_id = request.GET.get('department_id')

    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(employee__employee_id__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if dept_id and dept_id.isdigit():
        qs = qs.filter(employee__department_id=int(dept_id))

    import csv
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Role', 'Active', 'Employee ID', 'Department', 'Job Title', 'Joined'])

    for u in qs.order_by('-date_joined'):
        emp = getattr(u, 'employee', None)
        dept_name = getattr(getattr(emp, 'department', None), 'name', '') if emp else ''
        writer.writerow([
            u.id, u.username, u.email, u.get_full_name(), u.get_role_display(),
            'Yes' if u.is_active else 'No', getattr(emp, 'employee_id', ''), dept_name,
            getattr(emp, 'job_title', ''), u.date_joined.strftime('%Y-%m-%d %H:%M')
        ])

    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    return response

