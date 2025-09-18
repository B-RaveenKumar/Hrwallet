from django.urls import path
from . import views

app_name = 'hr_dashboard'

urlpatterns = [
    path('', views.dashboard, name='hr_dashboard'),
    path('employees/', views.manage_employees, name='hr_employees'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('leave-approvals/', views.leave_approvals, name='hr_leave_approvals'),
    path('attendance/', views.attendance_overview, name='hr_attendance'),
    path('departments/', views.departments, name='hr_departments'),
    path('biometric/', views.biometric_monitor, name='hr_biometric'),
    path('biometric/attendance/dashboard/', views.biometric_attendance_dashboard, name='biometric_attendance_dashboard'),


    # HR APIs: Leave approvals
    path('api/leaves/<int:pk>/status/', views.change_leave_status_api, name='change_leave_status_api'),
    path('api/leaves/bulk/', views.bulk_change_leaves_api, name='bulk_change_leaves_api'),
    path('api/leaves/export/', views.export_leaves_api, name='export_leaves_api'),

    # HR APIs: Attendance
    path('api/attendance/clock-in/', views.attendance_clock_in_api, name='attendance_clock_in_api'),
    path('api/attendance/clock-out/', views.attendance_clock_out_api, name='attendance_clock_out_api'),
    path('api/attendance/update/', views.update_attendance_api, name='update_attendance_api'),
    path('api/attendance/export/', views.export_attendance_api, name='export_attendance_api'),
]
