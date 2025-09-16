from django.contrib import admin
from .models import Company, Department, Employee, Attendance, LeaveRequest


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')  # Removed created_at as it doesn't exist
    search_fields = ('name', 'email')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager')  # Removed created_at as it might not exist
    search_fields = ('name', 'description')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'job_title', 'hire_date', 'is_active')
    list_filter = ('department', 'is_active', 'hire_date')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'job_title')
    date_hierarchy = 'hire_date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'clock_in', 'clock_out', 'total_hours', 'status')
    list_filter = ('status', 'date')
    search_fields = ('employee__user__username', 'employee__employee_id')
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status', 'created_at')
    list_filter = ('leave_type', 'status', 'created_at')
    search_fields = ('employee__user__username', 'employee__employee_id', 'reason')
    date_hierarchy = 'created_at'
