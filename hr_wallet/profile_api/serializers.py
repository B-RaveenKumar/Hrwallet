from rest_framework import serializers
from django.contrib.auth import get_user_model
from core_hr.models import Employee, Department, Company
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
