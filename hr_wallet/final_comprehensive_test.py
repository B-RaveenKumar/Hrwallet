#!/usr/bin/env python
"""
Final Comprehensive Test - Complete HR Wallet System Verification
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

User = get_user_model()

def final_comprehensive_test():
    """Final comprehensive test of the entire HR Wallet system"""
    print("🎯 FINAL COMPREHENSIVE HR WALLET SYSTEM TEST")
    print("=" * 70)
    
    client = Client()
    test_results = {
        'database_cleanup': False,
        'profile_creation_workflow': False,
        'user_authentication': False,
        'role_based_access': False,
        'api_endpoints': False,
        'frontend_forms': False,
        'data_relationships': False,
        'system_security': False
    }
    
    print("\n1️⃣ Database Cleanup Verification:")
    try:
        # Verify test users are removed
        test_users_exist = User.objects.filter(username__in=['testadmin', 'hrmanager', 'employee']).exists()
        if test_users_exist:
            print("   ❌ Test users still exist in database")
        else:
            print("   ✅ Test users successfully removed")
            test_results['database_cleanup'] = True
        
        # Check remaining data integrity
        total_users = User.objects.count()
        total_employees = Employee.objects.count()
        companies = Company.objects.count()
        departments = Department.objects.count()
        
        print(f"   Database state: {total_users} users, {total_employees} employees, {companies} companies, {departments} departments")
        
    except Exception as e:
        print(f"   ❌ Database verification error: {e}")
    
    print("\n2️⃣ Profile Creation Workflow Test:")
    try:
        # Test Super Admin creation of HR Manager
        super_admin = User.objects.filter(role='super_admin').first()
        if not super_admin:
            print("   ❌ No super admin found for testing")
        else:
            # Login as super admin
            super_admin.set_password('test123')
            super_admin.save()
            
            login_success = client.login(username=super_admin.username, password='test123')
            if login_success:
                # Test HR creation form
                response = client.get('/admin-panel/hr-managers/create/')
                if response.status_code == 200:
                    print("   ✅ Super Admin can access HR creation form")
                    
                    # Test HR creation API
                    company = Company.objects.first()
                    hr_dept = Department.objects.filter(company=company, name__icontains='hr').first()
                    
                    if hr_dept:
                        hr_data = {
                            'full_name': 'Test HR Manager Final',
                            'email': 'final.hr@test.com',
                            'phone': '+1-555-9999',
                            'role': 'hr_manager',
                            'department_id': hr_dept.id,
                            'designation': 'HR Manager',
                            'salary': 70000.00,
                            'employee_id': 'HRFINAL'
                        }
                        
                        response = client.post('/api/hr/', 
                                             data=json.dumps(hr_data), 
                                             content_type='application/json')
                        
                        if response.status_code == 201:
                            print("   ✅ Super Admin can create HR Managers via API")
                            
                            # Verify User-Employee relationship
                            try:
                                new_hr_user = User.objects.get(email='final.hr@test.com')
                                new_hr_employee = new_hr_user.employee
                                print("   ✅ User-Employee relationship properly established")
                                test_results['profile_creation_workflow'] = True
                                
                                # Test HR Manager can create Employee
                                client.logout()
                                new_hr_user.set_password('test123')
                                new_hr_user.save()
                                
                                hr_login = client.login(username=new_hr_user.username, password='test123')
                                if hr_login:
                                    response = client.get('/hr-dashboard/employees/create/')
                                    if response.status_code == 200:
                                        print("   ✅ HR Manager can access employee creation form")
                                        
                                        # Test employee creation
                                        it_dept = Department.objects.filter(company=company, name__icontains='it').first()
                                        if it_dept:
                                            emp_data = {
                                                'full_name': 'Test Employee Final',
                                                'email': 'final.emp@test.com',
                                                'phone': '+1-555-8888',
                                                'role': 'employee',
                                                'department_id': it_dept.id,
                                                'designation': 'Developer',
                                                'salary': 60000.00,
                                                'employee_id': 'EMPFINAL'
                                            }
                                            
                                            response = client.post('/api/employees/', 
                                                                 data=json.dumps(emp_data), 
                                                                 content_type='application/json')
                                            
                                            if response.status_code == 201:
                                                print("   ✅ HR Manager can create Employees via API")
                                            else:
                                                print(f"   ❌ Employee creation failed: {response.status_code}")
                                        
                                client.logout()
                            except Exception as e:
                                print(f"   ❌ User-Employee relationship error: {e}")
                        else:
                            print(f"   ❌ HR creation failed: {response.status_code}")
                    else:
                        print("   ⚠️  No HR department found for testing")
                else:
                    print(f"   ❌ HR creation form access failed: {response.status_code}")
            else:
                print("   ❌ Super admin login failed")
            
            client.logout()
    except Exception as e:
        print(f"   ❌ Profile creation workflow error: {e}")
    
    print("\n3️⃣ User Authentication Test:")
    try:
        # Test different user types can login
        test_users = [
            ('super_admin', '/admin-panel/'),
            ('hr_manager', '/hr-dashboard/'),
            ('employee', '/employee-portal/')
        ]
        
        auth_success = True
        for role, dashboard_url in test_users:
            user = User.objects.filter(role=role).first()
            if user:
                user.set_password('test123')
                user.save()
                
                login_success = client.login(username=user.username, password='test123')
                if login_success:
                    response = client.get(dashboard_url)
                    if response.status_code == 200:
                        print(f"   ✅ {role} can login and access dashboard")
                    else:
                        print(f"   ❌ {role} dashboard access failed: {response.status_code}")
                        auth_success = False
                else:
                    print(f"   ❌ {role} login failed")
                    auth_success = False
                
                client.logout()
            else:
                print(f"   ⚠️  No {role} user found for testing")
        
        test_results['user_authentication'] = auth_success
    except Exception as e:
        print(f"   ❌ Authentication test error: {e}")
    
    print("\n4️⃣ Role-Based Access Control Test:")
    try:
        # Test access restrictions
        employee_user = User.objects.filter(role='employee').first()
        if employee_user:
            employee_user.set_password('test123')
            employee_user.save()
            
            client.login(username=employee_user.username, password='test123')
            
            # Employee should not access admin panel
            response = client.get('/admin-panel/')
            if response.status_code == 403:
                print("   ✅ Employee correctly blocked from admin panel")
                
                # Employee should not access HR creation API
                response = client.get('/api/hr/list/')
                if response.status_code == 403:
                    print("   ✅ Employee correctly blocked from HR API")
                    test_results['role_based_access'] = True
                else:
                    print(f"   ❌ Employee access to HR API not blocked: {response.status_code}")
            else:
                print(f"   ❌ Employee access to admin panel not blocked: {response.status_code}")
            
            client.logout()
    except Exception as e:
        print(f"   ❌ Access control test error: {e}")
    
    print("\n5️⃣ API Endpoints Test:")
    try:
        # Test API endpoints with proper authentication
        super_admin = User.objects.filter(role='super_admin').first()
        if super_admin:
            client.login(username=super_admin.username, password='test123')
            
            api_tests = [
                ('/api/departments/', 'GET'),
                ('/api/hr/list/', 'GET'),
                ('/api/employees/list/', 'GET')
            ]
            
            api_success = True
            for url, method in api_tests:
                response = client.get(url) if method == 'GET' else client.post(url)
                if response.status_code == 200:
                    print(f"   ✅ {method} {url} working")
                else:
                    print(f"   ❌ {method} {url} failed: {response.status_code}")
                    api_success = False
            
            test_results['api_endpoints'] = api_success
            client.logout()
    except Exception as e:
        print(f"   ❌ API endpoints test error: {e}")
    
    print("\n6️⃣ Frontend Forms Test:")
    try:
        # Test frontend form accessibility
        super_admin = User.objects.filter(role='super_admin').first()
        hr_manager = User.objects.filter(role='hr_manager').first()
        
        forms_success = True
        
        if super_admin:
            client.login(username=super_admin.username, password='test123')
            response = client.get('/admin-panel/hr-managers/create/')
            if response.status_code == 200:
                print("   ✅ Super Admin HR creation form accessible")
            else:
                print(f"   ❌ Super Admin HR creation form failed: {response.status_code}")
                forms_success = False
            client.logout()
        
        if hr_manager:
            client.login(username=hr_manager.username, password='test123')
            response = client.get('/hr-dashboard/employees/create/')
            if response.status_code == 200:
                print("   ✅ HR Manager employee creation form accessible")
            else:
                print(f"   ❌ HR Manager employee creation form failed: {response.status_code}")
                forms_success = False
            client.logout()
        
        test_results['frontend_forms'] = forms_success
    except Exception as e:
        print(f"   ❌ Frontend forms test error: {e}")
    
    print("\n7️⃣ Data Relationships Test:")
    try:
        # Verify User-Employee relationships
        users_with_employees = 0
        total_users = User.objects.count()
        
        for user in User.objects.all():
            try:
                if hasattr(user, 'employee'):
                    users_with_employees += 1
            except:
                pass
        
        print(f"   Users with Employee profiles: {users_with_employees}/{total_users}")
        
        # Check for orphaned records
        employees_without_users = Employee.objects.filter(user__isnull=True).count()
        if employees_without_users == 0:
            print("   ✅ No orphaned Employee records found")
            test_results['data_relationships'] = True
        else:
            print(f"   ❌ Found {employees_without_users} orphaned Employee records")
            
    except Exception as e:
        print(f"   ❌ Data relationships test error: {e}")
    
    print("\n8️⃣ System Security Test:")
    try:
        # Test unauthenticated access
        response = client.get('/admin-panel/')
        if response.status_code in [302, 403]:  # Redirect to login or forbidden
            print("   ✅ Unauthenticated access properly blocked")
            
            # Test API without authentication
            response = client.post('/api/hr/', data=json.dumps({}), content_type='application/json')
            if response.status_code in [401, 403]:
                print("   ✅ API access without authentication properly blocked")
                test_results['system_security'] = True
            else:
                print(f"   ❌ API access without auth not blocked: {response.status_code}")
        else:
            print(f"   ❌ Unauthenticated access not blocked: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Security test error: {e}")
    
    # Final Results
    print("\n" + "=" * 70)
    print("🏆 FINAL COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():<35} → {status}")
    
    print(f"\n📊 Overall Score: {passed_tests}/{total_tests} tests passed")
    success_rate = (passed_tests / total_tests) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 SYSTEM VERIFICATION COMPLETE!")
        print("✅ HR Wallet is 100% functional!")
        print("🚀 Ready for production use!")
        print("\n🔑 Key Features Verified:")
        print("   • Test data cleanup completed")
        print("   • Profile creation workflow working")
        print("   • User authentication functional")
        print("   • Role-based access control enforced")
        print("   • API endpoints secure and working")
        print("   • Frontend forms accessible")
        print("   • Data relationships intact")
        print("   • System security implemented")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} issues found that need attention")
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = final_comprehensive_test()
    sys.exit(0 if success else 1)
