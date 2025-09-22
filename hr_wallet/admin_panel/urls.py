from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('company-admin-login/', views.company_admin_login, name='company_admin_login'),
    path('company-admin/', views.company_admin_dashboard, name='company_admin_dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('hr-managers/', views.manage_hr_managers, name='hr_managers'),
    path('hr-managers/create/', views.create_hr_manager, name='create_hr_manager'),
    path('settings/', views.system_settings, name='system_settings'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('biometric-devices/', views.biometric_devices, name='biometric_devices'),
]
