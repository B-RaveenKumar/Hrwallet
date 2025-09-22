#!/usr/bin/env python
"""
Comprehensive 500 Error Detection Script for HR Wallet Django Project
"""
import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth import authenticate

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from django.contrib.auth import get_user_model
from core_hr.models import Company, Department, Employee

User = get_user_model()

def test_all_urls():
    """Test all URLs systematically to identify 500 errors"""
    print("🔍 COMPREHENSIVE 500 ERROR DETECTION")
    print("=" * 60)
    
    client = Client()
    
    # Define all URLs to test
    test_urls = {
        'Public URLs': [
            '/',
            '/accounts/login/',
            '/accounts/logout/',
        ],
        'Super Admin URLs': [
            '/admin-panel/',
            '/admin-panel/users/',
            '/admin-panel/hr-managers/',
            '/admin-panel/hr-managers/create/',
            '/admin-panel/settings/',
            '/admin-panel/audit-logs/',
        ],
        'HR Manager URLs': [
            '/hr-dashboard/',
            '/hr-dashboard/employees/',
            '/hr-dashboard/employees/create/',
            '/hr-dashboard/departments/',
            '/hr-dashboard/leave-requests/',
            '/hr-dashboard/reports/',
        ],
        'Employee URLs': [
            '/employee-portal/',
            '/employee-portal/profile/',
            '/employee-portal/leave-requests/',
            '/employee-portal/payslips/',
            '/employee-portal/documents/',
        ],
        'API URLs': [
            '/api/departments/',
            '/api/employees/',
            '/api/hr/',
            '/api/employees/list/',
            '/api/hr/list/',
        ]
    }
    
    # Test credentials
    test_users = {
        'super_admin': {'username': 'testadmin', 'password': 'test123'},
        'hr_manager': {'username': 'hrmanager', 'password': 'test123'},
        'employee': {'username': 'employee', 'password': 'test123'}
    }
    
    errors_found = []
    
    # Test public URLs (no authentication)
    print("\n1️⃣ Testing Public URLs (No Authentication):")
    for url in test_urls['Public URLs']:
        try:
            response = client.get(url)
            status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
            print(f"   {url:<30} → {status}")
            if response.status_code >= 500:
                errors_found.append({
                    'url': url,
                    'user': 'anonymous',
                    'status_code': response.status_code,
                    'error': 'Server Error'
                })
        except Exception as e:
            print(f"   {url:<30} → ❌ Exception: {str(e)}")
            errors_found.append({
                'url': url,
                'user': 'anonymous',
                'status_code': 500,
                'error': str(e)
            })
    
    # Test authenticated URLs for each user role
    for role, credentials in test_users.items():
        print(f"\n2️⃣ Testing {role.upper()} URLs:")
        
        # Login
        login_success = client.login(**credentials)
        if not login_success:
            print(f"   ❌ Login failed for {role}")
            continue
        
        print(f"   ✅ Logged in as {role}")
        
        # Determine which URLs to test for this role
        if role == 'super_admin':
            urls_to_test = test_urls['Super Admin URLs'] + test_urls['API URLs']
        elif role == 'hr_manager':
            urls_to_test = test_urls['HR Manager URLs'] + test_urls['API URLs']
        else:  # employee
            urls_to_test = test_urls['Employee URLs'] + test_urls['API URLs']
        
        # Test URLs
        for url in urls_to_test:
            try:
                response = client.get(url)
                status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
                print(f"   {url:<35} → {status}")
                if response.status_code >= 500:
                    errors_found.append({
                        'url': url,
                        'user': role,
                        'status_code': response.status_code,
                        'error': 'Server Error'
                    })
            except Exception as e:
                print(f"   {url:<35} → ❌ Exception: {str(e)}")
                errors_found.append({
                    'url': url,
                    'user': role,
                    'status_code': 500,
                    'error': str(e)
                })
        
        # Test POST endpoints with sample data
        if role in ['super_admin', 'hr_manager']:
            print(f"   Testing POST endpoints for {role}:")
            
            # Test employee creation (for hr_manager and super_admin)
            if role == 'hr_manager':
                try:
                    response = client.post('/api/employees/', 
                                         data=json.dumps({
                                             'full_name': 'Test Employee',
                                             'email': 'test@example.com',
                                             'phone': '+1-555-0123',
                                             'role': 'employee',
                                             'department_id': 1,
                                             'designation': 'Developer',
                                             'salary': 50000.00,
                                             'employee_id': 'TEST001'
                                         }), 
                                         content_type='application/json')
                    status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
                    print(f"   POST /api/employees/              → {status}")
                    if response.status_code >= 500:
                        errors_found.append({
                            'url': 'POST /api/employees/',
                            'user': role,
                            'status_code': response.status_code,
                            'error': 'Server Error'
                        })
                except Exception as e:
                    print(f"   POST /api/employees/              → ❌ Exception: {str(e)}")
                    errors_found.append({
                        'url': 'POST /api/employees/',
                        'user': role,
                        'status_code': 500,
                        'error': str(e)
                    })
            
            # Test HR creation (for super_admin only)
            if role == 'super_admin':
                try:
                    response = client.post('/api/hr/', 
                                         data=json.dumps({
                                             'full_name': 'Test HR Manager',
                                             'email': 'testhr@example.com',
                                             'phone': '+1-555-0124',
                                             'role': 'hr_manager',
                                             'department_id': 1,
                                             'designation': 'HR Manager',
                                             'salary': 60000.00,
                                             'employee_id': 'HR001'
                                         }), 
                                         content_type='application/json')
                    status = "✅ OK" if response.status_code < 500 else f"❌ {response.status_code}"
                    print(f"   POST /api/hr/                     → {status}")
                    if response.status_code >= 500:
                        errors_found.append({
                            'url': 'POST /api/hr/',
                            'user': role,
                            'status_code': response.status_code,
                            'error': 'Server Error'
                        })
                except Exception as e:
                    print(f"   POST /api/hr/                     → ❌ Exception: {str(e)}")
                    errors_found.append({
                        'url': 'POST /api/hr/',
                        'user': role,
                        'status_code': 500,
                        'error': str(e)
                    })
        
        client.logout()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ERROR SUMMARY")
    print("=" * 60)
    
    if not errors_found:
        print("🎉 NO 500 ERRORS FOUND! All URLs are working correctly.")
    else:
        print(f"❌ Found {len(errors_found)} errors:")
        for i, error in enumerate(errors_found, 1):
            print(f"\n{i}. URL: {error['url']}")
            print(f"   User: {error['user']}")
            print(f"   Status: {error['status_code']}")
            print(f"   Error: {error['error']}")
    
    return errors_found

if __name__ == '__main__':
    test_all_urls()
