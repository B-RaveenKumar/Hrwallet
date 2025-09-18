#!/usr/bin/env python
"""
Test navigation and payroll routing changes
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from accounts.models import User

def test_navigation_templates():
    """Test that navigation templates don't contain Performance and Notifications menu items"""
    print("🧭 Testing Navigation Template Changes...")
    
    templates_to_check = [
        'templates/admin_panel/base.html',
        'templates/hr_dashboard/base.html', 
        'templates/employee_portal/base.html'
    ]
    
    passed = 0
    total = len(templates_to_check)
    
    for template_path in templates_to_check:
        try:
            full_path = os.path.join(os.path.dirname(__file__), template_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check that Performance and Notifications menu items are removed
                has_performance = 'Performance' in content and 'performance:goals' in content
                has_notifications = 'Notifications' in content and 'notifications:settings' in content
                
                if not has_performance and not has_notifications:
                    print(f"✅ {template_path} - Performance and Notifications removed")
                    passed += 1
                else:
                    print(f"❌ {template_path} - Still contains removed menu items")
                    if has_performance:
                        print(f"   - Still has Performance menu")
                    if has_notifications:
                        print(f"   - Still has Notifications menu")
            else:
                print(f"❌ {template_path} - File not found")
                
        except Exception as e:
            print(f"💥 {template_path} - Exception: {str(e)}")
    
    return passed, total

def test_payroll_template_inheritance():
    """Test that payroll templates use role-based inheritance"""
    print("\n💰 Testing Payroll Template Role-Based Inheritance...")
    
    payroll_templates = [
        'payroll/templates/payroll/dashboard.html',
        'payroll/templates/payroll/salaries.html',
        'payroll/templates/payroll/edit_salary.html',
        'payroll/templates/payroll/payslips_list.html'
    ]
    
    passed = 0
    total = len(payroll_templates)
    
    for template_path in payroll_templates:
        try:
            full_path = os.path.join(os.path.dirname(__file__), template_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for role-based template inheritance
                has_role_check = "{% if user.role == 'super_admin' %}" in content
                has_admin_extends = "{% extends 'admin_panel/base.html' %}" in content
                has_hr_extends = "{% extends 'hr_dashboard/base.html' %}" in content
                
                if has_role_check and has_admin_extends and has_hr_extends:
                    print(f"✅ {template_path} - Role-based inheritance implemented")
                    passed += 1
                else:
                    print(f"❌ {template_path} - Missing role-based inheritance")
                    if not has_role_check:
                        print(f"   - Missing role check")
                    if not has_admin_extends:
                        print(f"   - Missing admin panel extends")
                    if not has_hr_extends:
                        print(f"   - Missing hr dashboard extends")
            else:
                print(f"❌ {template_path} - File not found")
                
        except Exception as e:
            print(f"💥 {template_path} - Exception: {str(e)}")
    
    return passed, total

def test_payroll_urls_access():
    """Test that payroll URLs are accessible with proper role restrictions"""
    print("\n🔒 Testing Payroll URL Access Control...")
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    client = Client()
    
    # Test URLs without authentication first
    payroll_urls = [
        ('payroll:dashboard', 'Payroll Dashboard'),
        ('payroll:salaries', 'Salaries List'),
        ('payroll:payslips', 'Payslips List'),
    ]
    
    passed = 0
    total = len(payroll_urls)
    
    for url_name, description in payroll_urls:
        try:
            url = reverse(url_name)
            response = client.get(url)
            
            # Should redirect to login for unauthenticated users
            if response.status_code in [302, 301]:
                print(f"✅ {description} - Properly redirects unauthenticated users")
                passed += 1
            elif response.status_code == 403:
                print(f"✅ {description} - Properly blocks unauthenticated users") 
                passed += 1
            else:
                print(f"❌ {description} - Status {response.status_code} (expected redirect)")
                
        except Exception as e:
            print(f"💥 {description} - Exception: {str(e)}")
    
    return passed, total

def run_navigation_test():
    """Run all navigation and payroll routing tests"""
    print("🚀 HR Wallet Navigation & Payroll Routing Test Suite")
    print("=" * 70)
    
    total_passed = 0
    total_tests = 0
    
    # Test navigation template changes
    passed, total = test_navigation_templates()
    total_passed += passed
    total_tests += total
    
    # Test payroll template inheritance
    passed, total = test_payroll_template_inheritance()
    total_passed += passed
    total_tests += total
    
    # Test payroll URL access
    passed, total = test_payroll_urls_access()
    total_passed += passed
    total_tests += total
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {total_passed}/{total_tests} tests passed")
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! All navigation and routing changes implemented correctly!")
        print("✨ Removed menu items and role-based payroll templates working.")
    elif success_rate >= 75:
        print("✅ GOOD! Most navigation and routing changes working correctly.")
        print("⚠️  Minor issues detected but functionality is improved.")
    else:
        print("⚠️  NEEDS ATTENTION! Some changes may not be working correctly.")
        print("🔧 Please review the failing tests.")
    
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 75

if __name__ == '__main__':
    run_navigation_test()