from django.urls import path
from . import views
app_name = 'payroll'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('salaries/', views.list_salaries, name='salaries'),
    path('salaries/<int:employee_id>/edit/', views.edit_salary, name='edit_salary'),
    path('payslips/', views.list_payslips, name='payslips'),
    path('payslips/<int:pk>/pdf/', views.view_payslip_pdf, name='payslip_pdf'),
]

