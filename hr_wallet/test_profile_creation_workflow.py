#!/usr/bin/env python
"""
Profile Creation Workflow Test - Verify complete User-Employee creation process
"""
import os
import sys
import django
import json
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.contrib.auth import get_user_model
from core_hr.models import Employee, Company, Department
from django.db import transaction

User = get_user_model()

def test_profile_creation_workflow():
    """Test the complete profile creation workflow"""
    print("🧪 TESTING PROFILE CREATION WORKFLOW")
    print("=" * 60)
    
    client = Client()
    
    # First, we need to create a super admin to test with
    print("\n1️⃣ Setting up test environment:")
    
    # Get or create a company and department for testing
    company, created = Company.objects.get_or_create(
        name='Test Company',
        defaults={
            'address': '123 Test Street',
            'phone': '+1-555-0100',
            'email': 'test@company.com',
            'website': 'https://testcompany.com'
        }
    )
    print(f"   Company: {company.name} ({'created' if created else 'existing'})")
    
    # Create HR department if it doesn't exist
    hr_dept, created = Department.objects.get_or_create(
        company=company,
        name='Human Resources',
        defaults={
            'description': 'HR Department for testing'
        }
    )
    print(f"   HR Department: {hr_dept.name} ({'created' if created else 'existing'})")
    
    # Create IT department for employee testing
    it_dept, created = Department.objects.get_or_create(
        company=company,
        name='Information Technology',
        defaults={
            'description': 'IT Department for testing'
        }
    )
    print(f"   IT Department: {it_dept.name} ({'created' if created else 'existing'})")
    
    # Create a super admin user for testing
    try:
        super_admin = User.objects.get(username='testadmin')
        print(f"   Super Admin: {super_admin.username} (existing)")
    except User.DoesNotExist:
        super_admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='test123',
            first_name='Test',
            last_name='Admin',
            role='super_admin',
            company=company,
            is_active=True
        )
        print(f"   Super Admin: {super_admin.username} (created)")
    
    print("\n2️⃣ Testing Super Admin → HR Manager Creation:")
    
    # Login as super admin
    login_success = client.login(username='testadmin', password='test123')
    if not login_success:
        print("   ❌ Super admin login failed")
        return False
    print("   ✅ Super admin logged in successfully")
    
    # Test HR creation form page
    response = client.get('/admin-panel/hr-managers/create/')
    if response.status_code != 200:
        print(f"   ❌ HR creation form failed: {response.status_code}")
        return False
    print("   ✅ HR creation form page accessible")
    
    # Create HR Manager via API
    hr_data = {
        'full_name': 'John HR Manager',
        'email': 'john.hr@test.com',
        'phone': '+1-555-0201',
        'role': 'hr_manager',
        'department_id': hr_dept.id,
        'designation': 'Senior HR Manager',
        'salary': 75000.00,
        'employee_id': 'HR001'
    }
    
    response = client.post('/api/hr/', 
                         data=json.dumps(hr_data), 
                         content_type='application/json')
    
    if response.status_code != 201:
        print(f"   ❌ HR creation failed: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"      Error: {data.get('message')}")
            if 'errors' in data:
                for field, errors in data['errors'].items():
                    print(f"      {field}: {errors}")
        return False
    
    hr_response_data = response.json()
    print(f"   ✅ HR Manager created: {hr_response_data['data']['employee_id']}")
    print(f"      Name: {hr_response_data['data']['full_name']}")
    print(f"      Email: {hr_response_data['data']['email']}")
    print(f"      Default Password: {hr_response_data['data']['default_password']}")
    
    # Verify User and Employee records were created
    try:
        hr_user = User.objects.get(email='john.hr@test.com')
        hr_employee = hr_user.employee
        print(f"   ✅ User record created: {hr_user.username} (role: {hr_user.role})")
        print(f"   ✅ Employee record created: {hr_employee.employee_id}")
        print(f"   ✅ User-Employee relationship established")
    except (User.DoesNotExist, Employee.DoesNotExist) as e:
        print(f"   ❌ User or Employee record missing: {e}")
        return False
    
    client.logout()
    
    print("\n3️⃣ Testing HR Manager → Employee Creation:")
    
    # Login as the newly created HR manager
    # First set the password for the HR manager
    hr_user.set_password('test123')
    hr_user.save()
    
    login_success = client.login(username='john.hr@test.com', password='test123')
    if not login_success:
        print("   ❌ HR manager login failed")
        return False
    print("   ✅ HR manager logged in successfully")
    
    # Test employee creation form page
    response = client.get('/hr-dashboard/employees/create/')
    if response.status_code != 200:
        print(f"   ❌ Employee creation form failed: {response.status_code}")
        return False
    print("   ✅ Employee creation form page accessible")
    
    # Create Employee via API
    employee_data = {
        'full_name': 'Jane Employee',
        'email': 'jane.employee@test.com',
        'phone': '+1-555-0301',
        'role': 'employee',
        'department_id': it_dept.id,
        'designation': 'Software Developer',
        'salary': 65000.00,
        'employee_id': 'EMP001'
    }
    
    response = client.post('/api/employees/', 
                         data=json.dumps(employee_data), 
                         content_type='application/json')
    
    if response.status_code != 201:
        print(f"   ❌ Employee creation failed: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"      Error: {data.get('message')}")
            if 'errors' in data:
                for field, errors in data['errors'].items():
                    print(f"      {field}: {errors}")
        return False
    
    emp_response_data = response.json()
    print(f"   ✅ Employee created: {emp_response_data['data']['employee_id']}")
    print(f"      Name: {emp_response_data['data']['full_name']}")
    print(f"      Email: {emp_response_data['data']['email']}")
    print(f"      Default Password: {emp_response_data['data']['default_password']}")
    
    # Verify User and Employee records were created
    try:
        emp_user = User.objects.get(email='jane.employee@test.com')
        emp_employee = emp_user.employee
        print(f"   ✅ User record created: {emp_user.username} (role: {emp_user.role})")
        print(f"   ✅ Employee record created: {emp_employee.employee_id}")
        print(f"   ✅ User-Employee relationship established")
    except (User.DoesNotExist, Employee.DoesNotExist) as e:
        print(f"   ❌ User or Employee record missing: {e}")
        return False
    
    client.logout()
    
    print("\n4️⃣ Testing Login and Dashboard Access:")
    
    # Test HR Manager login and dashboard access
    login_success = client.login(username='john.hr@test.com', password='test123')
    if not login_success:
        print("   ❌ HR manager login failed")
        return False
    
    response = client.get('/hr-dashboard/')
    if response.status_code != 200:
        print(f"   ❌ HR dashboard access failed: {response.status_code}")
        return False
    print("   ✅ HR Manager can login and access dashboard")
    client.logout()
    
    # Test Employee login and portal access
    emp_user.set_password('test123')
    emp_user.save()
    
    login_success = client.login(username='jane.employee@test.com', password='test123')
    if not login_success:
        print("   ❌ Employee login failed")
        return False
    
    response = client.get('/employee-portal/')
    if response.status_code != 200:
        print(f"   ❌ Employee portal access failed: {response.status_code}")
        return False
    print("   ✅ Employee can login and access portal")
    client.logout()
    
    print("\n5️⃣ Final Database Verification:")
    
    # Check final database state
    total_users = User.objects.count()
    total_employees = Employee.objects.count()
    hr_managers = User.objects.filter(role='hr_manager').count()
    employees = User.objects.filter(role='employee').count()
    
    print(f"   Total Users: {total_users}")
    print(f"   Total Employees: {total_employees}")
    print(f"   HR Managers: {hr_managers}")
    print(f"   Regular Employees: {employees}")
    
    # Verify relationships
    users_with_employee_profiles = User.objects.filter(employee__isnull=False).count()
    print(f"   Users with Employee profiles: {users_with_employee_profiles}")
    
    print("\n" + "=" * 60)
    print("🎉 PROFILE CREATION WORKFLOW TEST COMPLETE!")
    print("✅ Super Admin can create HR Managers")
    print("✅ HR Managers can create Employees") 
    print("✅ User-Employee relationships are properly established")
    print("✅ Created users can login and access their dashboards")
    print("🚀 Profile creation system is fully functional!")
    
    return True

if __name__ == '__main__':
    success = test_profile_creation_workflow()
    sys.exit(0 if success else 1)
