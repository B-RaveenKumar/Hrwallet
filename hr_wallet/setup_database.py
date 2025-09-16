#!/usr/bin/env python
"""
Setup script to initialize HR Wallet database with sample data
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.contrib.auth import get_user_model
from core_hr.models import Company, Department, Employee
from django.utils import timezone

User = get_user_model()

def create_sample_data():
    """Create sample data for HR Wallet"""
    
    print("🚀 Setting up HR Wallet database...")
    
    # Create company
    company, created = Company.objects.get_or_create(
        name="HR Wallet Demo Company",
        defaults={
            'address': '123 Business Street, City, State 12345',
            'phone': '+1-555-0123',
            'email': 'info@hrwallet.com',
            'website': 'https://hrwallet.com'
        }
    )
    if created:
        print("✅ Created company: HR Wallet Demo Company")
    
    # Create departments
    departments_data = [
        {'name': 'Human Resources', 'description': 'HR management and employee relations'},
        {'name': 'Engineering', 'description': 'Software development and technical operations'},
        {'name': 'Sales', 'description': 'Sales and business development'},
        {'name': 'Marketing', 'description': 'Marketing and communications'},
        {'name': 'Finance', 'description': 'Financial management and accounting'},
    ]
    
    for dept_data in departments_data:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        if created:
            print(f"✅ Created department: {dept.name}")
    
    # Create users with different roles
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@hrwallet.com',
            'first_name': 'System',
            'last_name': 'Administrator',
            'role': 'super_admin',
            'password': 'admin123'
        },
        {
            'username': 'sarah.johnson',
            'email': 'sarah.johnson@hrwallet.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'hr_manager',
            'password': 'password123'
        },
        {
            'username': 'john.doe',
            'email': 'john.doe@hrwallet.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'employee',
            'password': 'password123'
        },
        {
            'username': 'jane.smith',
            'email': 'jane.smith@hrwallet.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'employee',
            'password': 'password123'
        },
        {
            'username': 'mike.wilson',
            'email': 'mike.wilson@hrwallet.com',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'role': 'employee',
            'password': 'password123'
        }
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
                'is_active': True
            }
        )
        
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"✅ Created user: {user.username} ({user.get_role_display()})")
        
        # Create employee profiles for non-admin users
        if user.role in ['hr_manager', 'employee'] and not hasattr(user, 'employee'):
            # Assign departments
            if user.role == 'hr_manager':
                department = Department.objects.get(name='Human Resources')
                job_title = 'HR Manager'
                employee_id = 'HR001'
            else:
                # Assign employees to different departments
                dept_names = ['Engineering', 'Sales', 'Marketing', 'Finance']
                dept_name = dept_names[hash(user.username) % len(dept_names)]
                department = Department.objects.get(name=dept_name)
                job_title = f'{dept_name} Specialist'
                employee_id = f'EMP{str(user.id).zfill(3)}'
            
            employee, emp_created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': employee_id,
                    'department': department,
                    'job_title': job_title,
                    'phone': f'+1-555-{str(user.id).zfill(4)}',
                    'hire_date': timezone.now().date(),
                    'salary': 50000 + (user.id * 5000),  # Varied salaries
                    'is_active': True
                }
            )
            
            if emp_created:
                print(f"✅ Created employee profile: {employee.employee_id} - {user.get_full_name()}")
    
    print("\n🎉 HR Wallet database setup completed successfully!")
    print("\n📋 Login Credentials:")
    print("=" * 50)
    print("Super Admin:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  Access: /admin-panel/")
    print()
    print("HR Manager:")
    print("  Username: sarah.johnson")
    print("  Password: password123")
    print("  Access: /hr-dashboard/")
    print()
    print("Employee:")
    print("  Username: john.doe")
    print("  Password: password123")
    print("  Access: /employee-portal/")
    print("=" * 50)
    print("\n🌐 Access the application at: http://127.0.0.1:8000")

if __name__ == '__main__':
    create_sample_data()
