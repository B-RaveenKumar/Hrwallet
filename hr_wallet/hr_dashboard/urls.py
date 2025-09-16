from django.urls import path
from . import views

app_name = 'hr_dashboard'

urlpatterns = [
    path('', views.dashboard, name='hr_dashboard'),
    path('employees/', views.manage_employees, name='hr_employees'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('leave-approvals/', views.leave_approvals, name='hr_leave_approvals'),
    path('attendance/', views.attendance_overview, name='hr_attendance'),
]
