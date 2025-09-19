from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from django.utils import timezone
from core_hr.models import Employee

TWOPL = Decimal('0.01')

class TaxBracket(models.Model):
    income_min = models.DecimalField(max_digits=12, decimal_places=2)
    income_max = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text='Percent rate, e.g. 10.00 for 10%')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['income_min']
        indexes = [models.Index(fields=['is_active', 'income_min', 'income_max'])]

    def __str__(self):
        return f"{self.income_min}-{self.income_max}@{self.tax_rate}%"

class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_percentage = models.BooleanField(default=False)
    amount_or_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    is_mandatory = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class EmployeeSalary(models.Model):
    SALARY_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.JSONField(default=dict, blank=True)
    effective_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=SALARY_STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_salaries')
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['employee', 'is_active', 'status']),
            models.Index(fields=['is_active', 'effective_date']),
        ]

    def total_allowances(self) -> Decimal:
        total = Decimal('0')
        for v in (self.allowances or {}).values():
            try:
                total += Decimal(str(v))
            except Exception:
                continue
        return total.quantize(TWOPL, rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        # If this salary is being activated, deactivate all others for the same employee
        if self.is_active and self.status == 'approved':
            EmployeeSalary.objects.filter(employee=self.employee).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class PaySlip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    generated_date = models.DateTimeField(auto_now_add=True)
    pdf_file_path = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        indexes = [models.Index(fields=['employee', 'pay_period_end'])]
        unique_together = [('employee', 'pay_period_start', 'pay_period_end')]
        ordering = ['-pay_period_end']

    def _progressive_tax(self, taxable: Decimal) -> Decimal:
        taxable = Decimal(taxable or 0)
        brackets = TaxBracket.objects.filter(is_active=True).order_by('income_min')
        tax = Decimal('0')
        for b in brackets:
            lower = Decimal(b.income_min)
            upper = Decimal(b.income_max)
            if taxable <= lower:
                break
            amount = min(taxable, upper) - lower
            rate = Decimal(b.tax_rate) / Decimal('100')
            if amount > 0:
                tax += (amount * rate)
        return tax.quantize(TWOPL, rounding=ROUND_HALF_UP)

    def calculate_totals(self, salary: EmployeeSalary):
        """Calculate payslip totals using provided salary record"""
        if not salary:
            self.gross_pay = Decimal('0.00')
            self.total_deductions = Decimal('0.00')
            self.net_pay = Decimal('0.00')
            return

        base = Decimal(salary.basic_salary)
        allowances = salary.total_allowances()
        gross = base + allowances

        # Mandatory deductions
        deductions = Decimal('0')
        for d in DeductionType.objects.filter(is_active=True, is_mandatory=True):
            if d.is_percentage:
                deductions += (gross * (Decimal(d.amount_or_percentage) / Decimal('100')))
            else:
                deductions += Decimal(d.amount_or_percentage)

        # Progressive tax on gross
        tax = self._progressive_tax(gross)
        deductions += tax

        self.gross_pay = gross.quantize(TWOPL, rounding=ROUND_HALF_UP)
        self.total_deductions = deductions.quantize(TWOPL, rounding=ROUND_HALF_UP)
        self.net_pay = (self.gross_pay - self.total_deductions).quantize(TWOPL, rounding=ROUND_HALF_UP)

    def calculate_amounts(self):
        """Calculate payslip amounts based on employee's active salary"""
        try:
            # Get the employee's active salary that was effective during the pay period
            salary = EmployeeSalary.objects.filter(
                employee=self.employee,
                is_active=True,
                status='approved',
                effective_date__lte=self.pay_period_end
            ).order_by('-effective_date').first()

            if not salary:
                # Fallback to employee's basic salary field if no salary record exists
                basic = Decimal(self.employee.salary or '0')
                if basic > 0:
                    # Create a temporary salary-like object for calculation
                    class TempSalary:
                        def __init__(self, basic_salary):
                            self.basic_salary = Decimal(str(basic_salary))
                            self.allowances = {}

                        def total_allowances(self):
                            return Decimal('0')

                    temp_salary = TempSalary(basic)
                    # Type ignore for temporary object
                    self.calculate_totals(temp_salary)  # type: ignore
                else:
                    # No salary information available
                    self.gross_pay = Decimal('0.00')
                    self.total_deductions = Decimal('0.00')
                    self.net_pay = Decimal('0.00')
            else:
                self.calculate_totals(salary)

        except Exception as e:
            # Fallback calculation with error logging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating payslip amounts for {self.employee}: {str(e)}")
            self.gross_pay = Decimal('0.00')
            self.total_deductions = Decimal('0.00')
            self.net_pay = Decimal('0.00')

    def generate_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            import os
            from django.conf import settings as dj_settings
        except Exception:
            # Fallback: leave blank; UI can show HTML slip
            return None
        media_root = getattr(dj_settings, 'MEDIA_ROOT', None)
        if not media_root:
            return None
        payslips_dir = os.path.join(media_root, 'payslips')
        os.makedirs(payslips_dir, exist_ok=True)
        filename = f"payslips/{self.employee.employee_id}-{self.pay_period_end}.pdf"
        fullpath = os.path.join(media_root, filename)
        c = canvas.Canvas(fullpath, pagesize=A4)
        c.drawString(72, 800, f"Payslip: {self.employee.user.get_full_name()} ({self.employee.employee_id})")
        c.drawString(72, 780, f"Period: {self.pay_period_start} to {self.pay_period_end}")
        c.drawString(72, 760, f"Gross: {self.gross_pay}")
        c.drawString(72, 740, f"Deductions: {self.total_deductions}")
        c.drawString(72, 720, f"Net: {self.net_pay}")
        c.showPage(); c.save()
        self.pdf_file_path = filename
        self.save(update_fields=['pdf_file_path'])
        return self.pdf_file_path

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user} - {self.action} at {self.timestamp}'

