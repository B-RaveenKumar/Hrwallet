from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from decimal import Decimal


class Company(models.Model):
    """Company model - updated to match actual database schema"""
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.CharField(max_length=200, default='')
    logo = models.CharField(max_length=100, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    max_employees = models.PositiveIntegerField(default=100)
    slug = models.CharField(max_length=200, default='')
    subscription_plan = models.CharField(max_length=50, default='basic')

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_employee_count(self):
        """Get number of active employees in this company"""
        try:
            return self.employees.filter(is_active=True).count()
        except Exception:
            return 0

    def __str__(self):
        return self.name

    def get_employee_count(self):
        """Get total number of active employees"""
        return self.employees.filter(is_active=True).count()

    def get_department_count(self):
        """Get total number of departments"""
        return self.departments.count()


class Department(models.Model):
    """Department model with multi-company support"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['company', 'name']
        ordering = ['company', 'name']

    def __str__(self):
        company_name = self.company.name if self.company else "No Company"
        return f"{company_name} - {self.name}"

    def get_employee_count(self):
        """Get number of active employees in this department"""
        return self.employees.filter(is_active=True).count()


class Employee(models.Model):
    """Employee profile extending User model with multi-company support"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    employee_id = models.CharField(max_length=20)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    job_title = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    hire_date = models.DateField(default=timezone.now)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'employee_id']
        ordering = ['company', 'employee_id']

    def get_current_month_hours(self):
        """Get total hours worked in current month"""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        return WorkHours.objects.filter(
            employee=self,
            date__gte=start_of_month,
            date__lte=today
        ).aggregate(total=Sum('total_hours'))['total'] or 0

    def get_leave_balance(self):
        """Get employee leave balance"""
        try:
            return self.leavebalance
        except LeaveBalance.DoesNotExist:
            return None  # Return None instead of auto-creating

    def get_pending_leave_requests(self):
        """Get count of pending leave requests"""
        return self.leaverequest_set.filter(status='pending').count()

    def get_attendance_percentage(self, days=30):
        """Get attendance percentage for last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        total_days = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lte=end_date
        ).count()

        present_days = Attendance.objects.filter(
            employee=self,
            date__gte=start_date,
            date__lte=end_date,
            status__in=['present', 'late']
        ).count()

        if total_days == 0:
            return 0
        return round((present_days / total_days) * 100, 1)

    def get_latest_payroll(self):
        """Get latest payroll record"""
        return self.payroll_set.order_by('-pay_period_end').first()

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"


class Attendance(models.Model):
    """Employee attendance tracking"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    break_duration = models.DurationField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('half_day', 'Half Day'),
        ],
        default='present'
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee} - {self.date}"


class LeaveRequest(models.Model):
    """Employee leave requests"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(
        max_length=20,
        choices=[
            ('annual', 'Annual Leave'),
            ('sick', 'Sick Leave'),
            ('personal', 'Personal Leave'),
            ('maternity', 'Maternity Leave'),
            ('emergency', 'Emergency Leave'),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"


class Payroll(models.Model):
    """Employee payroll records"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    insurance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('processed', 'Processed'),
            ('paid', 'Paid'),
        ],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'pay_period_start', 'pay_period_end']

    def save(self, *args, **kwargs):
        self.gross_pay = self.basic_salary + self.allowances + self.overtime_pay
        self.total_deductions = self.tax_deduction + self.insurance_deduction + self.other_deductions
        self.net_pay = self.gross_pay - self.total_deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.pay_period_start} to {self.pay_period_end}"


class LeaveBalance(models.Model):
    """Employee leave balance tracking"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    annual_leave_total = models.PositiveIntegerField(default=21)
    annual_leave_used = models.PositiveIntegerField(default=0)
    sick_leave_total = models.PositiveIntegerField(default=10)
    sick_leave_used = models.PositiveIntegerField(default=0)
    personal_leave_total = models.PositiveIntegerField(default=5)
    personal_leave_used = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def annual_leave_remaining(self):
        return self.annual_leave_total - self.annual_leave_used

    @property
    def sick_leave_remaining(self):
        return self.sick_leave_total - self.sick_leave_used

    @property
    def personal_leave_remaining(self):
        return self.personal_leave_total - self.personal_leave_used

    def __str__(self):
        return f"{self.employee} - Leave Balance"


class WorkHours(models.Model):
    """Employee work hours tracking"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    regular_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    break_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'date']

    def save(self, *args, **kwargs):
        self.total_hours = self.regular_hours + self.overtime_hours
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.total_hours}h)"



class BiometricDevice(models.Model):
    """Represents a biometric device (e.g., ZKTeco) for attendance integration."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='biometric_devices')
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50, default='ZKTeco')
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(default=4370)
    # ZKTeco Communication Key (COM key). Usually 0..999999. 0 by default.
    comm_key = models.PositiveIntegerField(default=0)
    timezone = models.CharField(max_length=64, default='UTC')
    api_key = models.CharField(max_length=128, help_text='Shared secret for device push/auth')
    webhook_secret = models.CharField(max_length=128, blank=True, help_text='Optional secret for cloud webhook HMAC')
    cloud_endpoint_url = models.URLField(blank=True)
    push_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_pull = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['company', 'serial_number']),
            models.Index(fields=['company', 'ip_address']),
            models.Index(fields=['company', 'is_active']),
        ]
        unique_together = [('company', 'serial_number')]
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.company.name} - {self.name} ({self.brand} {self.model})"


class BiometricUserMap(models.Model):
    """Maps a device-specific user ID (or global cloud user ID) to an Employee."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='biometric_user_maps')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='biometric_ids')
    device = models.ForeignKey(BiometricDevice, on_delete=models.CASCADE, null=True, blank=True, related_name='user_maps')
    device_user_id = models.CharField(max_length=100, help_text='ID on the device (enrolled ID)')
    global_user_id = models.CharField(max_length=100, blank=True, help_text='Cloud/global user ID if applicable')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['company', 'device', 'device_user_id']),
            models.Index(fields=['company', 'global_user_id']),
        ]
        unique_together = [
            ('company', 'device', 'device_user_id'),
        ]

    def __str__(self):
        return f"{self.employee} -> {self.device or 'GLOBAL'}:{self.device_user_id or self.global_user_id}"


class BiometricEvent(models.Model):
    """Raw biometric punch events for auditing and idempotent processing."""
    EVENT_TYPES = (
        ('checkin', 'Check In'),
        ('checkout', 'Check Out'),
        ('unknown', 'Unknown'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='biometric_events')
    device = models.ForeignKey(BiometricDevice, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    device_user_id = models.CharField(max_length=100)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='unknown')
    timestamp = models.DateTimeField()
    external_event_id = models.CharField(max_length=128, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    attendance = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True, related_name='biometric_events')
    dedupe_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['company', 'device_user_id', 'timestamp']),
            models.Index(fields=['processed']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device_user_id} {self.event_type} @ {self.timestamp}"
