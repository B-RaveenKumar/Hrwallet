from django.urls import path
from . import views

app_name = 'profile_api'

urlpatterns = [
    # Employee management endpoints
    path('employees/', views.create_employee, name='create_employee'),
    path('employees/list/', views.list_employees, name='list_employees'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/update/', views.update_employee, name='update_employee'),
    path('employees/<int:pk>/status/', views.change_employee_status, name='change_employee_status'),
    path('employees/bulk/', views.bulk_update_employees, name='bulk_update_employees'),
    path('employees/export/', views.export_employees, name='export_employees'),


    # HR management endpoints
    path('hr/', views.create_hr, name='create_hr'),
    path('hr/list/', views.list_hr, name='list_hr'),

    # Utility endpoints
    path('departments/', views.list_departments, name='list_departments'),
    path('departments/create/', views.create_department, name='create_department'),
    path('departments/<int:pk>/update/', views.update_department, name='update_department'),
    path('departments/<int:pk>/status/', views.change_department_status, name='change_department_status'),


    # Biometric integration endpoints
    path('biometric/events/ingest/', views.ingest_biometric_event, name='ingest_biometric_event'),
    path('biometric/heartbeat/', views.biometric_heartbeat, name='biometric_heartbeat'),
    path('biometric/devices/', views.list_biometric_devices, name='list_biometric_devices'),
    path('biometric/devices/register/', views.register_biometric_device, name='register_biometric_device'),
    path('biometric/devices/<int:pk>/update/', views.update_biometric_device, name='update_biometric_device'),
    path('biometric/mappings/upsert/', views.upsert_biometric_mapping, name='upsert_biometric_mapping'),
    path('biometric/status/', views.biometric_status, name='biometric_status'),
    path('biometric/events/recent/', views.list_recent_biometric_events, name='list_recent_biometric_events'),

    # Biometric attendance management endpoints
    path('biometric/attendance/', views.biometric_attendance_list, name='biometric_attendance_list'),
    path('biometric/attendance/<int:pk>/', views.biometric_attendance_edit, name='biometric_attendance_edit'),
    path('biometric/attendance/bulk-edit/', views.biometric_attendance_bulk_edit, name='biometric_attendance_bulk_edit'),
    path('biometric/mappings/<int:pk>/correct/', views.biometric_user_map_correction, name='biometric_user_map_correction'),


    # Biometric device management extras
    path('biometric/devices/<int:pk>/delete/', views.delete_biometric_device, name='delete_biometric_device'),
    path('biometric/devices/<int:pk>/ping/', views.ping_biometric_device, name='ping_biometric_device'),
    path('biometric/devices/<int:pk>/sync/', views.sync_biometric_device, name='sync_biometric_device'),

    # Salary Management
    path('salaries/', views.list_employee_salaries, name='list_employee_salaries'),
    path('salaries/create/', views.create_employee_salary, name='create_employee_salary'),
    path('salaries/<int:salary_id>/update/', views.update_employee_salary, name='update_employee_salary'),
    path('salaries/<int:salary_id>/approve/', views.approve_salary, name='approve_salary'),

]
