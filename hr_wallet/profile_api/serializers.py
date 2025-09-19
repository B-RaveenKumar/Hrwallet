from rest_framework import serializers
from django.contrib.auth import get_user_model
from core_hr.models import Employee, Department, Company, BiometricEvent, BiometricUserMap
from payroll.models import EmployeeSalary
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']


class EmployeeCreateSerializer(serializers.Serializer):
    """Serializer for creating employee profiles"""
    full_name = serializers.CharField(max_length=200, help_text="Full name of the employee")
    email = serializers.EmailField(help_text="Email address (must be unique)")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="Phone number")
    role = serializers.ChoiceField(choices=['employee'], default='employee', help_text="Role (Staff only)")
    department_id = serializers.IntegerField(help_text="Department ID")
    designation = serializers.CharField(max_length=100, help_text="Job title/designation")
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, help_text="Salary amount")
    employee_id = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="Employee ID (auto-generated if not provided)")

    # Enhanced salary configuration fields
    basic_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, help_text="Basic salary amount")
    allowances = serializers.JSONField(required=False, default=dict, help_text="Allowances as JSON object")
    salary_effective_date = serializers.DateField(required=False, allow_null=True, help_text="Salary effective date")
    salary_notes = serializers.CharField(max_length=500, required=False, allow_blank=True, help_text="Notes about salary configuration")

    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_department_id(self, value):
        """Validate department exists and belongs to user's company"""
        request = self.context.get('request')
        if not request or not request.user.company:
            raise serializers.ValidationError("Invalid company context.")

        try:
            department = Department.objects.get(id=value, company=request.user.company, is_active=True)
            return value
        except Department.DoesNotExist:
            raise serializers.ValidationError("Invalid department or department not found in your company.")

    def validate_employee_id(self, value):
        """Validate employee ID uniqueness within company"""
        if value:
            request = self.context.get('request')
            if request and request.user.company:
                if Employee.objects.filter(employee_id=value, company=request.user.company).exists():
                    raise serializers.ValidationError("An employee with this ID already exists in your company.")
        return value


class HRCreateSerializer(serializers.Serializer):
    """Serializer for creating HR profiles"""
    full_name = serializers.CharField(max_length=200, help_text="Full name of the HR person")
    email = serializers.EmailField(help_text="Email address (must be unique)")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="Phone number")
    role = serializers.ChoiceField(choices=['hr_manager'], default='hr_manager', help_text="Role (HR Manager only)")
    department_id = serializers.IntegerField(help_text="Department ID")
    designation = serializers.CharField(max_length=100, help_text="Job title/designation")
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, help_text="Salary amount")
    employee_id = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="Employee ID (auto-generated if not provided)")

    # Enhanced salary configuration fields
    basic_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, help_text="Basic salary amount")
    allowances = serializers.JSONField(required=False, default=dict, help_text="Allowances as JSON object")
    salary_effective_date = serializers.DateField(required=False, allow_null=True, help_text="Salary effective date")
    salary_notes = serializers.CharField(max_length=500, required=False, allow_blank=True, help_text="Notes about salary configuration")

    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_department_id(self, value):
        """Validate department exists and belongs to user's company"""
        request = self.context.get('request')
        if not request or not request.user.company:
            raise serializers.ValidationError("Invalid company context.")

        try:
            department = Department.objects.get(id=value, company=request.user.company, is_active=True)
            return value
        except Department.DoesNotExist:
            raise serializers.ValidationError("Invalid department or department not found in your company.")

    def validate_employee_id(self, value):
        """Validate employee ID uniqueness within company"""
        if value:
            request = self.context.get('request')
            if request and request.user.company:
                if Employee.objects.filter(employee_id=value, company=request.user.company).exists():
                    raise serializers.ValidationError("An employee with this ID already exists in your company.")
        return value


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for listing employees"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'email', 'phone', 'role',
            'department_name', 'job_title', 'salary', 'hire_date', 'is_active',
            'created_at', 'updated_at'
        ]


class EmployeeSalarySerializer(serializers.ModelSerializer):
    """Serializer for employee salary management"""
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    total_allowances = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeSalary
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'basic_salary',
            'allowances', 'total_allowances', 'effective_date', 'status',
            'is_active', 'created_at', 'updated_at', 'created_by',
            'created_by_name', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get_total_allowances(self, obj):
        """Calculate total allowances"""
        return obj.total_allowances()


class SalaryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employee salaries"""

    class Meta:
        model = EmployeeSalary
        fields = [
            'employee', 'basic_salary', 'allowances', 'effective_date',
            'status', 'is_active'
        ]

    def validate_basic_salary(self, value):
        """Validate basic salary is positive"""
        if value <= 0:
            raise serializers.ValidationError("Basic salary must be greater than 0")
        return value

    def validate_effective_date(self, value):
        """Validate effective date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Effective date cannot be in the past")
        return value


class HRListSerializer(serializers.ModelSerializer):
    """Serializer for listing HR managers"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'email', 'phone', 'role',
            'department_name', 'job_title', 'salary', 'hire_date', 'is_active',
            'created_at', 'updated_at'
        ]



class EmployeeDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    department_id = serializers.IntegerField(source='department.id', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'first_name', 'last_name', 'email', 'role',
            'phone', 'address', 'date_of_birth', 'department_id', 'department_name',
            'job_title', 'salary', 'hire_date', 'is_active', 'created_at', 'updated_at'
        ]


class EmployeeUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False)
    department_id = serializers.IntegerField(required=False)
    job_title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    def validate_email(self, value):
        request = self.context.get('request')
        employee = self.context.get('employee')
        User = get_user_model()
        if value and employee and value != employee.user.email:
            if User.objects.filter(email=value).exclude(id=employee.user.id).exists():
                raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_department_id(self, value):
        request = self.context.get('request')
        if value is None:
            return value
        try:
            Department.objects.get(id=value, company=request.user.company, is_active=True)
            return value
        except Department.DoesNotExist:
            raise serializers.ValidationError('Invalid department for your company.')

class BiometricEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricEvent
        fields = [
            'id', 'company', 'device', 'device_user_id', 'event_type', 'timestamp',
            'external_event_id', 'raw_payload', 'processed', 'attendance', 'dedupe_hash', 'created_at'
        ]
        read_only_fields = ['id', 'company', 'created_at', 'dedupe_hash']

    def validate_timestamp(self, value):
        # Ensure punch times are reasonable (not in future, not too far past)
        now = timezone.now()
        if value > now:
            raise serializers.ValidationError('Punch time cannot be in the future.')
        if (now - value).days > 60:
            raise serializers.ValidationError('Punch time is too far in the past.')
        return value

    def update(self, instance, validated_data):
        # Audit trail: log who edited and when
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        old_data = {field: getattr(instance, field) for field in validated_data}
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Log audit (could be to a model or external system)
        if user:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"User {user.username} edited BiometricEvent {instance.id}: {old_data}"
            )
        return instance

class BiometricEventBulkEditSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), help_text='IDs of BiometricEvents to edit')
    event_type = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(required=False)
    device_user_id = serializers.CharField(required=False)

    def validate(self, attrs):
        # Add custom validation for bulk edits
        if not attrs.get('ids'):
            raise serializers.ValidationError('No event IDs provided for bulk edit.')
        return attrs

class BiometricUserMapCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricUserMap
        fields = ['id', 'employee', 'device', 'device_user_id', 'global_user_id']

    def update(self, instance, validated_data):
        # Audit trail for mapping correction
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        old_data = {field: getattr(instance, field) for field in validated_data}
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if user:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"User {user.username} edited BiometricUserMap {instance.id}: {old_data}"
            )
        return instance
