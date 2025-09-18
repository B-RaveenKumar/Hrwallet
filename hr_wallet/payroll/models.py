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
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.JSONField(default=dict, blank=True)
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-effective_date']
        indexes = [models.Index(fields=['is_active', 'effective_date'])]

    def total_allowances(self) -> Decimal:
        total = Decimal('0')
        for v in (self.allowances or {}).values():
            try:
                total += Decimal(str(v))
            except Exception:
                continue
        return total.quantize(TWOPL, rounding=ROUND_HALF_UP)

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

    def calculate_totals(self, salary: EmployeeSalary, month_days: int = 30):
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

