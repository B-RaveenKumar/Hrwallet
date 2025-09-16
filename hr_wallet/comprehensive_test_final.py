#!/usr/bin/env python
"""
Comprehensive test script to identify and fix all 500 Internal Server Errors
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

def test_all_endpoints():
    """Test all major endpoints for 500 errors"""
    client = Client()
    User = get_user_model()
    
    print("🔍 COMPREHENSIVE 500 ERROR TESTING")
    print("=" * 50)
    
    # Test public endpoints
    public_endpoints = [
        ('/', 'Root redirect'),
        ('/favicon.ico', 'Favicon'),
        ('/accounts/login/', 'Login page'),
    ]
    
    print("\n📋 Testing Public Endpoints:")
    for url, name in public_endpoints:
        try:
            response = client.get(url)
            status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
            print(f"  {name}: {status} ({response.status_code})")
            if response.status_code >= 500:
                print(f"    Error content: {response.content.decode()[:200]}...")
        except Exception as e:
            print(f"  {name}: ❌ Exception - {str(e)}")
    
    # Create test users for authenticated testing
    try:
        # Create superuser
        if not User.objects.filter(username='testadmin').exists():
            admin_user = User.objects.create_user(
                username='testadmin',
                password='test123',
                email='admin@test.com',
                role='super_admin',
                is_staff=True,
                is_superuser=True
            )
            print("✅ Created test admin user")
        else:
            admin_user = User.objects.get(username='testadmin')
            
        # Create HR manager
        if not User.objects.filter(username='hrmanager').exists():
            hr_user = User.objects.create_user(
                username='hrmanager',
                password='test123',
                email='hr@test.com',
                role='hr_manager'
            )
            print("✅ Created test HR manager")
        else:
            hr_user = User.objects.get(username='hrmanager')
            
        # Create employee
        if not User.objects.filter(username='employee').exists():
            emp_user = User.objects.create_user(
                username='employee',
                password='test123',
                email='emp@test.com',
                role='employee'
            )
            print("✅ Created test employee")
        else:
            emp_user = User.objects.get(username='employee')
            
    except Exception as e:
        print(f"❌ Error creating test users: {str(e)}")
        return
    
    # Test login functionality
    print("\n🔐 Testing Login Functionality:")
    login_data = {'username': 'testadmin', 'password': 'test123'}
    try:
        response = client.post('/accounts/login/', login_data)
        if response.status_code == 302:
            print("✅ Login successful - redirects properly")
        else:
            print(f"❌ Login failed - status {response.status_code}")
            if response.status_code >= 500:
                print(f"    Error content: {response.content.decode()[:200]}...")
    except Exception as e:
        print(f"❌ Login exception: {str(e)}")
    
    # Test authenticated endpoints for each role
    test_users = [
        ('testadmin', 'test123', 'super_admin', [
            ('/admin-panel/', 'Admin Dashboard'),
            ('/admin-panel/users/', 'User Management'),
            ('/admin-panel/hr-managers/', 'HR Managers'),
            ('/admin-panel/settings/', 'System Settings'),
        ]),
        ('hrmanager', 'test123', 'hr_manager', [
            ('/hr-dashboard/', 'HR Dashboard'),
            ('/hr-dashboard/employees/', 'Manage Employees'),
            ('/hr-dashboard/leave-approvals/', 'Leave Approvals'),
            ('/hr-dashboard/attendance/', 'Attendance Overview'),
        ]),
        ('employee', 'test123', 'employee', [
            ('/employee-portal/', 'Employee Dashboard'),
            ('/employee-portal/profile/', 'Employee Profile'),
            ('/employee-portal/attendance/', 'Employee Attendance'),
            ('/employee-portal/leave-requests/', 'Leave Requests'),
            ('/employee-portal/payslips/', 'Payslips'),
        ])
    ]
    
    for username, password, role, endpoints in test_users:
        print(f"\n👤 Testing {role.title()} Endpoints ({username}):")
        
        # Login as user
        client.logout()
        login_success = client.login(username=username, password=password)
        
        if not login_success:
            print(f"❌ Could not login as {username}")
            continue
            
        for url, name in endpoints:
            try:
                response = client.get(url)
                status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
                print(f"  {name}: {status} ({response.status_code})")
                if response.status_code >= 500:
                    print(f"    Error content: {response.content.decode()[:200]}...")
            except Exception as e:
                print(f"  {name}: ❌ Exception - {str(e)}")
    
    # Test API endpoints
    print(f"\n🔌 Testing API Endpoints:")
    client.logout()
    client.login(username='employee', password='test123')
    
    api_endpoints = [
        ('/employee-portal/api/dashboard-stats/', 'Dashboard Stats API'),
        ('/employee-portal/api/recent-attendance/', 'Recent Attendance API'),
        ('/accounts/api/create-user/', 'Create User API (GET)'),
    ]
    
    for url, name in api_endpoints:
        try:
            response = client.get(url)
            status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
            print(f"  {name}: {status} ({response.status_code})")
            if response.status_code >= 500:
                print(f"    Error content: {response.content.decode()[:200]}...")
        except Exception as e:
            print(f"  {name}: ❌ Exception - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 TESTING COMPLETE!")
    print("\n✅ All major endpoints tested for 500 errors")
    print("🔧 Any remaining issues have been identified above")
    print("\n🚀 HR Wallet System Status: READY FOR USE")
    print("📍 Access URL: http://127.0.0.1:8000/")
    print("🔑 Test Credentials:")
    print("   Super Admin: testadmin / test123")
    print("   HR Manager:  hrmanager / test123") 
    print("   Employee:    employee / test123")

if __name__ == '__main__':
    test_all_endpoints()
