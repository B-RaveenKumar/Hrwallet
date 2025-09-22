#!/usr/bin/env python
"""
Setup test data for HR Wallet system - FOR TESTING ONLY
This script creates sample data for testing purposes.
In production, use the manual profile creation system instead.
"""
import os
import sys
import django
from django.utils import timezone
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.contrib.auth import get_user_model
from core_hr.models import Company, Department, Employee, LeaveBalance

def setup_test_data():
    """Create test data for the HR Wallet system"""
    User = get_user_model()
    
    print("🔧 Setting up test data for HR Wallet...")
    
    # Create or get default company
    try:
        company, created = Company.objects.get_or_create(
            name='HR Wallet System',
            defaults={
                'address': '123 Business Street, Tech City, TC 12345',
                'phone': '+1-555-0123',
                'email': 'info@hrwallet.com',
                'website': 'https://hrwallet.com',
                'logo': '',
                'is_active': True,
                'max_employees': 500,
                'slug': 'hr-wallet-system',
                'subscription_plan': 'enterprise',
            }
        )
        if created:
            print(f"✅ Created company: {company.name}")
        else:
            print(f"✅ Using existing company: {company.name}")
    except Exception as e:
        print(f"❌ Error creating company: {str(e)}")
        return
    
    # Create departments
    departments_data = [
        {'name': 'Human Resources', 'description': 'HR Department'},
        {'name': 'Information Technology', 'description': 'IT Department'},
        {'name': 'Finance', 'description': 'Finance Department'},
        {'name': 'Operations', 'description': 'Operations Department'},
    ]
    
    departments = {}
    for dept_data in departments_data:
        try:
            dept, created = Department.objects.get_or_create(
                company=company,
                name=dept_data['name'],
                defaults={
                    'description': dept_data['description'],
                    'is_active': True,
                }
            )
            departments[dept_data['name']] = dept
            if created:
                print(f"✅ Created department: {dept.name}")
        except Exception as e:
            print(f"❌ Error creating department {dept_data['name']}: {str(e)}")
    
    # Create test users and employee profiles
    test_users = [
        {
            'username': 'testadmin',
            'email': 'admin@hrwallet.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'super_admin',
            'is_staff': True,
            'is_superuser': True,
            'employee_data': {
                'employee_id': 'ADM001',
                'job_title': 'System Administrator',
                'department': 'Information Technology',
                'salary': Decimal('75000.00'),
                'phone': '+1-555-0101',
            }
        },
        {
            'username': 'hrmanager',
            'email': 'hr@hrwallet.com',
            'first_name': 'HR',
            'last_name': 'Manager',
            'role': 'hr_manager',
            'employee_data': {
                'employee_id': 'HR001',
                'job_title': 'HR Manager',
                'department': 'Human Resources',
                'salary': Decimal('65000.00'),
                'phone': '+1-555-0102',
            }
        },
        {
            'username': 'employee',
            'email': 'emp@hrwallet.com',
            'first_name': 'John',
            'last_name': 'Employee',
            'role': 'employee',
            'employee_data': {
                'employee_id': 'EMP001',
                'job_title': 'Software Developer',
                'department': 'Information Technology',
                'salary': Decimal('55000.00'),
                'phone': '+1-555-0103',
            }
        }
    ]
    
    for user_data in test_users:
        try:
            # Create or update user
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                    'company': company,
                }
            )
            
            if created:
                user.set_password('test123')
                user.save()
                print(f"✅ Created user: {user.username}")
            else:
                # Update existing user
                user.company = company
                user.role = user_data['role']
                user.save()
                print(f"✅ Updated user: {user.username}")
            
            # Create or update employee profile
            emp_data = user_data['employee_data']
            department = departments.get(emp_data['department'])
            
            employee, emp_created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'company': company,
                    'employee_id': emp_data['employee_id'],
                    'department': department,
                    'job_title': emp_data['job_title'],
                    'salary': emp_data['salary'],
                    'phone': emp_data['phone'],
                    'hire_date': timezone.now().date(),
                    'is_active': True,
                }
            )
            
            if emp_created:
                print(f"✅ Created employee profile: {employee.employee_id}")
                
                # Create leave balance for employee
                leave_balance, lb_created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    defaults={
                        'annual_leave_total': 20,
                        'annual_leave_used': 0,
                        'sick_leave_total': 10,
                        'sick_leave_used': 0,
                        'personal_leave_total': 5,
                        'personal_leave_used': 0,
                    }
                )
                if lb_created:
                    print(f"✅ Created leave balance for: {employee.employee_id}")
            else:
                # Update existing employee
                employee.company = company
                employee.department = department
                employee.is_active = True
                employee.save()
                print(f"✅ Updated employee profile: {employee.employee_id}")
                
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 TEST DATA SETUP COMPLETE!")
    print("\n✅ Created/Updated:")
    print(f"   • Company: {company.name}")
    print(f"   • Departments: {len(departments)}")
    print(f"   • Users: {len(test_users)}")
    print(f"   • Employee Profiles: {len(test_users)}")
    print("\n🔑 Test Credentials:")
    print("   Super Admin: testadmin / test123")
    print("   HR Manager:  hrmanager / test123")
    print("   Employee:    employee / test123")
    print("\n🚀 System ready for testing!")

if __name__ == '__main__':
    setup_test_data()
