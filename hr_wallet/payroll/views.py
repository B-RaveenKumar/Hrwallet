from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
from accounts.decorators import require_roles
from core_hr.models import Employee
from .models import EmployeeSalary, PaySlip

@require_roles('super_admin', 'hr_manager')
@login_required
def dashboard(request):
    slips = PaySlip.objects.order_by('-pay_period_end')[:20]
    template_name = 'payroll/admin_dashboard.html' if request.user.role == 'super_admin' else 'payroll/dashboard.html'
    return render(request, template_name, {'recent_slips': slips})

@require_roles('super_admin', 'hr_manager')
@login_required
def list_salaries(request):
    # Filter by company for security
    salaries = EmployeeSalary.objects.filter(
        employee__company=request.user.company
    ).select_related('employee__user', 'employee__department', 'created_by', 'updated_by').order_by('-effective_date')

    # Add search and filter functionality
    search = request.GET.get('search', '')
    if search:
        salaries = salaries.filter(
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search) |
            Q(employee__employee_id__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        salaries = salaries.filter(status=status_filter)

    is_active_filter = request.GET.get('is_active', '')
    if is_active_filter:
        salaries = salaries.filter(is_active=is_active_filter.lower() == 'true')

    template_name = 'payroll/admin_salaries.html' if request.user.role == 'super_admin' else 'payroll/salaries.html'
    context = {
        'salaries': salaries,
        'search': search,
        'status_filter': status_filter,
        'is_active_filter': is_active_filter,
        'status_choices': EmployeeSalary.SALARY_STATUS_CHOICES,
    }
    return render(request, template_name, context)

@require_roles('super_admin', 'hr_manager')
@login_required
def edit_salary(request, employee_id):
    emp = get_object_or_404(Employee, id=employee_id, company=request.user.company)

    # Get the current active salary or create a new one
    current_salary = EmployeeSalary.objects.filter(
        employee=emp, is_active=True
    ).order_by('-effective_date').first()

    if request.method == 'POST':
        basic_salary = Decimal(request.POST.get('basic_salary') or '0')
        allowances = {}

        # Parse allowances from form
        for key in request.POST:
            if key.startswith('allowance_'):
                allowance_name = key.replace('allowance_', '')
                allowance_value = request.POST.get(key, '0')
                if allowance_value:
                    allowances[allowance_name] = allowance_value

        effective_date = request.POST.get('effective_date')
        if effective_date:
            from datetime import datetime
            effective_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
        else:
            effective_date = timezone.now().date()

        # Create new salary record (for audit trail)
        new_salary = EmployeeSalary.objects.create(
            employee=emp,
            basic_salary=basic_salary,
            allowances=allowances,
            effective_date=effective_date,
            status='approved',  # Auto-approve for HR/Admin
            is_active=True,
            created_by=request.user,
            updated_by=request.user
        )

        # Deactivate previous salary records
        EmployeeSalary.objects.filter(
            employee=emp
        ).exclude(pk=new_salary.pk).update(is_active=False)

        messages.success(request, f'Salary updated successfully for {emp.user.get_full_name()}')
        return redirect('payroll:salaries')

    # Get salary history for display
    salary_history = EmployeeSalary.objects.filter(
        employee=emp
    ).order_by('-effective_date')[:5]

    template_name = 'payroll/admin_edit_salary.html' if request.user.role == 'super_admin' else 'payroll/edit_salary.html'
    context = {
        'employee': emp,
        'salary': current_salary,
        'salary_history': salary_history,
        'allowance_types': ['housing', 'transport', 'medical', 'food', 'communication', 'other']
    }
    return render(request, template_name, context)

@login_required
def list_payslips(request):
    if request.user.role in ('super_admin', 'hr_manager'):
        slips = PaySlip.objects.select_related('employee__user').order_by('-pay_period_end')
        template_name = 'payroll/admin_payslips_list.html' if request.user.role == 'super_admin' else 'payroll/payslips_list.html'
    else:
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return HttpResponseForbidden()
        slips = PaySlip.objects.filter(employee=emp).order_by('-pay_period_end')
        template_name = 'payroll/payslips_list.html'
    return render(request, template_name, {'slips': slips})

@login_required
def view_payslip_pdf(request, pk):
    slip = get_object_or_404(PaySlip, pk=pk)
    if request.user.role not in ('super_admin', 'hr_manager'):
        if getattr(request.user, 'employee', None) != slip.employee:
            return HttpResponseForbidden()
    if not slip.pdf_file_path:
        slip.generate_pdf()
    from django.conf import settings
    import os
    path = os.path.join(settings.MEDIA_ROOT, slip.pdf_file_path) if slip.pdf_file_path else None
    if path and os.path.exists(path):
        return FileResponse(open(path, 'rb'), content_type='application/pdf')
    return render(request, 'payroll/payslip_html.html', {'slip': slip})

