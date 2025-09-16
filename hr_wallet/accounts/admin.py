from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role-based fields
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Security', {
            'fields': ('role', 'created_by', 'last_password_change'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Security', {
            'fields': ('role', 'created_by'),
        }),
    )
    
    readonly_fields = ('last_password_change', 'date_joined', 'last_login')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Super admins can see all users
        if request.user.is_superuser:
            return qs
        # HR managers can only see employees
        elif request.user.role == 'hr_manager':
            return qs.filter(role='employee')
        # Employees can only see themselves
        else:
            return qs.filter(id=request.user.id)
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        
        # Super admins can edit anyone
        if request.user.is_superuser:
            return True
        
        # HR managers can edit employees
        if request.user.role == 'hr_manager' and obj.role == 'employee':
            return True
        
        # Users can edit themselves
        if request.user == obj:
            return True
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return request.user.is_superuser
        
        # Only super admins can delete users
        return request.user.is_superuser
