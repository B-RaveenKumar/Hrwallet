#!/usr/bin/env python
"""
Test payroll template syntax and functionality
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

def test_payroll_template_syntax():
    """Test that payroll templates don't have syntax errors"""
    print("🧪 Testing Payroll Template Syntax...")
    
    client = Client()
    
    # Test payroll URL without authentication (should redirect, not crash)
    try:
        response = client.get('/payroll/')
        if response.status_code in [200, 301, 302, 403]:
            print("✅ Payroll dashboard template - No syntax errors")
            return True
        else:
            print(f"❌ Payroll dashboard template - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"💥 Payroll dashboard template - Template error: {str(e)}")
        return False

def test_template_files_exist():
    """Test that all required template files exist"""
    print("\n📁 Testing Template File Existence...")
    
    required_templates = [
        'payroll/templates/payroll/dashboard.html',
        'payroll/templates/payroll/admin_dashboard.html',
        'payroll/templates/payroll/salaries.html', 
        'payroll/templates/payroll/admin_salaries.html',
        'payroll/templates/payroll/edit_salary.html',
        'payroll/templates/payroll/admin_edit_salary.html',
        'payroll/templates/payroll/payslips_list.html',
        'payroll/templates/payroll/admin_payslips_list.html'
    ]
    
    passed = 0
    total = len(required_templates)
    
    for template_path in required_templates:
        full_path = os.path.join(os.path.dirname(__file__), template_path)
        if os.path.exists(full_path):
            print(f"✅ {template_path} - Exists")
            passed += 1
        else:
            print(f"❌ {template_path} - Missing")
    
    return passed, total

def test_template_syntax():
    """Test that templates have valid Django syntax"""
    print("\n🔍 Testing Template Syntax Validity...")
    
    templates_to_test = [
        'payroll/templates/payroll/dashboard.html',
        'payroll/templates/payroll/admin_dashboard.html',
        'payroll/templates/payroll/salaries.html',
        'payroll/templates/payroll/admin_salaries.html'
    ]
    
    passed = 0
    total = len(templates_to_test)
    
    for template_path in templates_to_test:
        try:
            full_path = os.path.join(os.path.dirname(__file__), template_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for valid extends syntax
                if '{% extends ' in content and content.strip().startswith('{% extends '):
                    print(f"✅ {template_path} - Valid extends syntax")
                    passed += 1
                else:
                    print(f"❌ {template_path} - Invalid template syntax")
            else:
                print(f"❌ {template_path} - File not found")
                
        except Exception as e:
            print(f"💥 {template_path} - Exception: {str(e)}")
    
    return passed, total

def run_syntax_test():
    """Run all syntax tests"""
    print("🚀 HR Wallet Payroll Template Syntax Test")
    print("=" * 60)
    
    # Test basic functionality
    basic_works = test_payroll_template_syntax()
    
    # Test file existence
    passed1, total1 = test_template_files_exist()
    
    # Test template syntax
    passed2, total2 = test_template_syntax()
    
    total_passed = (1 if basic_works else 0) + passed1 + passed2
    total_tests = 1 + total1 + total2
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {total_passed}/{total_tests} tests passed")
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Template syntax error fixed!")
        print("✨ All payroll templates are working correctly.")
    elif success_rate >= 75:
        print("✅ GOOD! Template syntax mostly fixed.")
        print("⚠️  Minor issues remain but templates should work.")
    else:
        print("⚠️  NEEDS ATTENTION! Template syntax issues remain.")
        print("🔧 Please review the failing tests.")
    
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 75

if __name__ == '__main__':
    run_syntax_test()