from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from .decorators import audit_action
from .models import User
from core_hr.models import Company, Department, Employee, LeaveBalance
import logging
import json

logger = logging.getLogger(__name__)


# Company selection view removed - direct login flow implemented


@csrf_protect
@never_cache
@audit_action('login_attempt')
def login_view(request):
    """
    Simplified login view with direct authentication - no company selection required
    """
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    # Get or create default company for system operation
    default_company = None
    try:
        default_company = Company.objects.first()
        if not default_company:
            default_company, created = Company.objects.get_or_create(
                name='HR Wallet System',
                defaults={
                    'address': '123 Business Street',
                    'phone': '+1-555-0123',
                    'email': 'info@hrwallet.com',
                }
            )
    except Exception as e:
        logger.error(f"Error accessing company data: {str(e)}")
        # Continue without company - system will work without it

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

            # 3) Try by employee_id (EMP0001/HR0001 style)
            if user is None:
                try:
                    emp = Employee.objects.filter(employee_id=username_input).select_related('user').first()
                    if emp and emp.user:
                        user = authenticate(request, username=emp.user.username, password=password)
                except Exception:
                    pass

            if user is not None:
                if user.is_active:
                    # Assign default company to user if they don't have one
                    if default_company and hasattr(user, 'company') and not user.company:
                        try:
                            user.company = default_company
                            user.save()
                        except Exception as e:
                            logger.warning(f"Could not assign company to user {username_input}: {str(e)}")

                    login(request, user)
                    # Get role safely
                    role = getattr(user, 'role', 'employee')
                    company_name = getattr(default_company, 'name', 'HR Wallet System') if default_company else 'HR Wallet System'
                    logger.info(f"Successful login: {user.username} (role: {role}) at {company_name}")

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
        'page_title': 'Login to HR Wallet'
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
