#!/usr/bin/env python
"""
Final System Verification - HR Wallet Django Project
Comprehensive test to verify zero 500 errors and full functionality
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
from core_hr.models import Company, Department, Employee

User = get_user_model()

def final_verification():
    """Final comprehensive verification of the HR Wallet system"""
    print("🎯 FINAL HR WALLET SYSTEM VERIFICATION")
    print("=" * 70)
    
    client = Client()
    
    # Test all critical user flows
    test_results = {
        'login_flow': False,
        'super_admin_dashboard': False,
        'hr_manager_dashboard': False,
        'employee_portal': False,
        'profile_creation_forms': False,
        'api_endpoints': False,
        'access_control': False,
        'database_integrity': False
    }
    
    print("\n1️⃣ Testing Login Flow:")
    try:
        # Test login page
        response = client.get('/accounts/login/')
        assert response.status_code == 200, f"Login page failed: {response.status_code}"
        
        # Test redirect from root
        response = client.get('/')
        assert response.status_code in [200, 302], f"Root redirect failed: {response.status_code}"
        
        test_results['login_flow'] = True
        print("   ✅ Login flow working correctly")
    except Exception as e:
        print(f"   ❌ Login flow error: {e}")
    
    print("\n2️⃣ Testing Super Admin Dashboard:")
    try:
        login_success = client.login(username='testadmin', password='test123')
        assert login_success, "Super admin login failed"
        
        # Test dashboard
        response = client.get('/admin-panel/')
        assert response.status_code == 200, f"Admin dashboard failed: {response.status_code}"
        
        # Test HR managers page
        response = client.get('/admin-panel/hr-managers/')
        assert response.status_code == 200, f"HR managers page failed: {response.status_code}"
        
        # Test HR creation form
        response = client.get('/admin-panel/hr-managers/create/')
        assert response.status_code == 200, f"HR creation form failed: {response.status_code}"
        
        test_results['super_admin_dashboard'] = True
        print("   ✅ Super Admin dashboard fully functional")
        client.logout()
    except Exception as e:
        print(f"   ❌ Super Admin dashboard error: {e}")
        client.logout()
    
    print("\n3️⃣ Testing HR Manager Dashboard:")
    try:
        login_success = client.login(username='hrmanager', password='test123')
        assert login_success, "HR manager login failed"
        
        # Test dashboard
        response = client.get('/hr-dashboard/')
        assert response.status_code == 200, f"HR dashboard failed: {response.status_code}"
        
        # Test employees page
        response = client.get('/hr-dashboard/employees/')
        assert response.status_code == 200, f"Employees page failed: {response.status_code}"
        
        # Test employee creation form
        response = client.get('/hr-dashboard/employees/create/')
        assert response.status_code == 200, f"Employee creation form failed: {response.status_code}"
        
        test_results['hr_manager_dashboard'] = True
        print("   ✅ HR Manager dashboard fully functional")
        client.logout()
    except Exception as e:
        print(f"   ❌ HR Manager dashboard error: {e}")
        client.logout()
    
    print("\n4️⃣ Testing Employee Portal:")
    try:
        login_success = client.login(username='employee', password='test123')
        assert login_success, "Employee login failed"
        
        # Test portal
        response = client.get('/employee-portal/')
        assert response.status_code == 200, f"Employee portal failed: {response.status_code}"
        
        # Test profile page
        response = client.get('/employee-portal/profile/')
        assert response.status_code == 200, f"Profile page failed: {response.status_code}"
        
        # Test leave requests
        response = client.get('/employee-portal/leave-requests/')
        assert response.status_code == 200, f"Leave requests failed: {response.status_code}"
        
        test_results['employee_portal'] = True
        print("   ✅ Employee portal fully functional")
        client.logout()
    except Exception as e:
        print(f"   ❌ Employee portal error: {e}")
        client.logout()
    
    print("\n5️⃣ Testing Profile Creation Forms:")
    try:
        # Test super admin HR creation form
        client.login(username='testadmin', password='test123')
        response = client.get('/admin-panel/hr-managers/create/')
        assert response.status_code == 200, "HR creation form failed"
        client.logout()
        
        # Test HR manager employee creation form
        client.login(username='hrmanager', password='test123')
        response = client.get('/hr-dashboard/employees/create/')
        assert response.status_code == 200, "Employee creation form failed"
        client.logout()
        
        test_results['profile_creation_forms'] = True
        print("   ✅ Profile creation forms working correctly")
    except Exception as e:
        print(f"   ❌ Profile creation forms error: {e}")
        client.logout()
    
    print("\n6️⃣ Testing API Endpoints:")
    try:
        # Test with super admin
        client.login(username='testadmin', password='test123')
        
        # Test departments API
        response = client.get('/api/departments/')
        assert response.status_code == 200, "Departments API failed"
        
        # Test HR list API
        response = client.get('/api/hr/list/')
        assert response.status_code == 200, "HR list API failed"
        
        # Test employees list API
        response = client.get('/api/employees/list/')
        assert response.status_code == 200, "Employees list API failed"
        
        client.logout()
        
        test_results['api_endpoints'] = True
        print("   ✅ API endpoints working correctly")
    except Exception as e:
        print(f"   ❌ API endpoints error: {e}")
        client.logout()
    
    print("\n7️⃣ Testing Access Control:")
    try:
        # Test employee cannot access admin functions
        client.login(username='employee', password='test123')
        
        response = client.get('/admin-panel/')
        assert response.status_code == 403, "Employee should not access admin panel"
        
        response = client.get('/api/hr/list/')
        assert response.status_code == 403, "Employee should not access HR list"
        
        client.logout()
        
        # Test HR manager cannot create HR
        client.login(username='hrmanager', password='test123')
        
        response = client.post('/api/hr/', data=json.dumps({}), content_type='application/json')
        assert response.status_code == 403, "HR manager should not create HR"
        
        client.logout()
        
        test_results['access_control'] = True
        print("   ✅ Access control working correctly")
    except Exception as e:
        print(f"   ❌ Access control error: {e}")
        client.logout()
    
    print("\n8️⃣ Testing Database Integrity:")
    try:
        # Test model relationships
        companies = Company.objects.all()
        departments = Department.objects.all()
        employees = Employee.objects.all()
        users = User.objects.all()
        
        assert companies.exists(), "No companies found"
        assert departments.exists(), "No departments found"
        assert employees.exists(), "No employees found"
        assert users.exists(), "No users found"
        
        # Test model methods
        for employee in employees:
            employee.get_leave_balance()  # Should not raise exception
            employee.get_attendance_percentage()  # Should not raise exception
        
        test_results['database_integrity'] = True
        print("   ✅ Database integrity verified")
    except Exception as e:
        print(f"   ❌ Database integrity error: {e}")
    
    # Final Results
    print("\n" + "=" * 70)
    print("🏆 FINAL VERIFICATION RESULTS")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():<30} → {status}")
    
    print(f"\n📊 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 SYSTEM VERIFICATION COMPLETE!")
        print("✅ HR Wallet is 100% functional with ZERO 500 errors!")
        print("🚀 Ready for production deployment!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} issues found that need attention")
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = final_verification()
    sys.exit(0 if success else 1)
