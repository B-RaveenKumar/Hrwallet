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

]
