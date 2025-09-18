from django.contrib import admin
from .models import PaySlip, TaxBracket, DeductionType, EmployeeSalary

@admin.register(PaySlip)
class PaySlipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period_start', 'pay_period_end', 'gross_pay', 'net_pay')
    list_filter = ('pay_period_end',)
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'employee__user__last_name')

@admin.register(TaxBracket)
class TaxBracketAdmin(admin.ModelAdmin):
    list_display = ('income_min', 'income_max', 'tax_rate', 'is_active')
    list_filter = ('is_active',)

@admin.register(DeductionType)
class DeductionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_percentage', 'amount_or_percentage', 'is_mandatory', 'is_active')
    list_filter = ('is_active', 'is_mandatory')

@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'basic_salary', 'effective_date', 'is_active')
    list_filter = ('is_active',)

