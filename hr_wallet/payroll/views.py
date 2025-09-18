from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponseForbidden
from django.utils import timezone
from decimal import Decimal
from accounts.decorators import require_roles
from core_hr.models import Employee
from .models import EmployeeSalary, PaySlip

@require_roles('super_admin', 'hr_manager')
@login_required
def dashboard(request):
    slips = PaySlip.objects.order_by('-pay_period_end')[:20]
    return render(request, 'payroll/dashboard.html', {'recent_slips': slips})

@require_roles('super_admin', 'hr_manager')
@login_required
def list_salaries(request):
    salaries = EmployeeSalary.objects.select_related('employee__user').order_by('-effective_date')
    return render(request, 'payroll/salaries.html', {'salaries': salaries})

@require_roles('super_admin', 'hr_manager')
@login_required
def edit_salary(request, employee_id):
    emp = get_object_or_404(Employee, id=employee_id)
    sal, _ = EmployeeSalary.objects.get_or_create(employee=emp, defaults={'basic_salary': Decimal('0.00')})
    if request.method == 'POST':
        sal.basic_salary = Decimal(request.POST.get('basic_salary') or '0')
        sal.allowances = {'allowance': request.POST.get('allowance') or '0'}
        sal.updated_by = request.user
        sal.save()
        return redirect('payroll:salaries')
    return render(request, 'payroll/edit_salary.html', {'employee': emp, 'salary': sal})

@login_required
def list_payslips(request):
    if request.user.role in ('super_admin', 'hr_manager'):
        slips = PaySlip.objects.select_related('employee__user').order_by('-pay_period_end')
    else:
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return HttpResponseForbidden()
        slips = PaySlip.objects.filter(employee=emp).order_by('-pay_period_end')
    return render(request, 'payroll/payslips_list.html', {'slips': slips})

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

