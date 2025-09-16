from django.urls import path
from . import views

app_name = 'employee_portal'

urlpatterns = [
    path('', views.dashboard, name='employee_dashboard'),
    path('profile/', views.profile, name='employee_profile'),
    path('attendance/', views.attendance, name='employee_attendance'),
    path('leave-requests/', views.leave_requests, name='employee_leave_requests'),
    path('payslips/', views.payslips, name='employee_payslips'),

    # API endpoints for live updates
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/recent-attendance/', views.api_recent_attendance, name='api_recent_attendance'),
    path('api/update-profile/', views.api_update_profile, name='api_update_profile'),
]
