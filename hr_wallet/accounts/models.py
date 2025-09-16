from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with role-based access control and multi-company support
    """
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('hr_manager', 'HR Manager'),
        ('super_admin', 'Super Administrator'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        help_text='User role determines access permissions'
    )

    # Multi-company support (nullable for backward compatibility)
    company = models.ForeignKey(
        'core_hr.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='Company this user belongs to'
    )

    # Additional fields for security and audit
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        help_text='User who created this account'
    )

    last_password_change = models.DateTimeField(
        default=timezone.now,
        help_text='Last time password was changed'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active.'
    )
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def can_access_admin_panel(self):
        """Check if user can access admin panel"""
        return self.role == 'super_admin'
    
    @property
    def can_access_hr_dashboard(self):
        """Check if user can access HR dashboard"""
        return self.role == 'hr_manager'
    
    @property
    def can_access_employee_portal(self):
        """Check if user can access employee portal"""
        return self.role == 'employee'
    
    @property
    def is_super_admin(self):
        """Check if user is super admin"""
        return self.role == 'super_admin'
    
    @property
    def is_hr_manager(self):
        """Check if user is HR manager"""
        return self.role == 'hr_manager'
    
    @property
    def is_employee(self):
        """Check if user is employee"""
        return self.role == 'employee'
    
    def get_dashboard_url(self):
        """Get the appropriate dashboard URL for user's role"""
        if self.is_super_admin:
            return '/admin-panel/'
        elif self.is_hr_manager:
            return '/hr-dashboard/'
        elif self.is_employee:
            return '/employee-portal/'
        else:
            return '/dashboard/'
    
    def save(self, *args, **kwargs):
        # Set superuser status for super_admin role
        if self.role == 'super_admin':
            self.is_staff = True
            self.is_superuser = True
        elif self.role == 'hr_manager':
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        
        super().save(*args, **kwargs)
