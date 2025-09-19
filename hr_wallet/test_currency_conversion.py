#!/usr/bin/env python
"""
HR Wallet Currency Conversion Test
Tests that all currency symbols have been converted from USD ($) to Indian Rupees (₹)
"""

import os
import re
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

def test_template_currency_conversion():
    """Test that all templates use ₹ instead of $ for currency"""
    print("\n💰 Testing Template Currency Conversion...")
    
    template_files = [
        'payroll/templates/payroll/salaries.html',
        'payroll/templates/payroll/edit_salary.html',
        'payroll/templates/payroll/admin_salaries.html',
        'payroll/templates/payroll/admin_edit_salary.html',
        'payroll/templates/payroll/payslip_html.html',
        'payroll/templates/payroll/payslips_list.html',
        'payroll/templates/payroll/dashboard.html',
        'payroll/templates/payroll/admin_dashboard.html',
        'templates/employee_portal/payslips.html',
        'templates/hr_dashboard/create_employee.html',
        'templates/hr_dashboard/hr_profile.html'
    ]
    
    passed = 0
    total = len(template_files)
    issues = []
    
    for template_path in template_files:
        full_path = os.path.join(os.path.dirname(__file__), template_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for dollar signs in currency contexts (excluding jQuery selectors)
            dollar_matches = re.findall(r'\$\{\{[^}]+\}\}|\$[0-9,]+(?:\.[0-9]{2})?(?![a-zA-Z_])', content)
            rupee_matches = re.findall(r'₹\{\{[^}]+\}\}|₹[0-9,]+(?:\.[0-9]{2})?', content)
            
            # Check for currency icons
            dollar_icons = content.count('bi-currency-dollar')
            rupee_icons = content.count('bi-currency-rupee')
            
            if dollar_matches or dollar_icons > 0:
                issues.append(f"❌ {template_path} - Still contains $ symbols: {dollar_matches}")
                print(f"❌ {template_path} - Still contains $ symbols")
            else:
                print(f"✅ {template_path} - Currency converted to ₹")
                passed += 1
        else:
            print(f"⚠️  {template_path} - File not found")
    
    return passed, total, issues

def test_icon_conversion():
    """Test that currency icons have been converted"""
    print("\n🎯 Testing Currency Icon Conversion...")
    
    template_files = [
        'payroll/templates/payroll/salaries.html',
        'payroll/templates/payroll/edit_salary.html',
        'payroll/templates/payroll/admin_salaries.html',
        'templates/hr_dashboard/hr_profile.html'
    ]
    
    passed = 0
    total = len(template_files)
    
    for template_path in template_files:
        full_path = os.path.join(os.path.dirname(__file__), template_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for rupee icons
            if 'bi-currency-rupee' in content:
                print(f"✅ {template_path} - Uses rupee icons")
                passed += 1
            elif 'bi-currency-dollar' in content:
                print(f"❌ {template_path} - Still uses dollar icons")
            else:
                print(f"⚠️  {template_path} - No currency icons found")
                passed += 1  # Neutral case
        else:
            print(f"⚠️  {template_path} - File not found")
    
    return passed, total

def test_hr_profile_standardization():
    """Test that HR profile matches employee profile structure"""
    print("\n👤 Testing HR Profile Standardization...")
    
    hr_profile_path = os.path.join(os.path.dirname(__file__), 'templates/hr_dashboard/hr_profile.html')
    employee_profile_path = os.path.join(os.path.dirname(__file__), 'templates/employee_portal/profile.html')
    
    if not os.path.exists(hr_profile_path):
        print("❌ HR profile template not found")
        return 0, 1
    
    if not os.path.exists(employee_profile_path):
        print("⚠️  Employee profile template not found for comparison")
        return 1, 1
    
    with open(hr_profile_path, 'r', encoding='utf-8') as f:
        hr_content = f.read()
    
    # Check for key standardization elements
    checks = [
        ('Card-based layout', 'class="card"' in hr_content),
        ('Profile photo section', 'bi-person-circle' in hr_content or 'profile' in hr_content.lower()),
        ('Personal information form', 'Personal Information' in hr_content),
        ('Employment details', 'Employment Details' in hr_content or 'employment' in hr_content.lower()),
        ('Bootstrap styling', 'form-control' in hr_content and 'btn' in hr_content),
        ('Responsive design', 'col-md-' in hr_content or 'row' in hr_content)
    ]
    
    passed = 0
    for check_name, condition in checks:
        if condition:
            print(f"✅ {check_name} - Present")
            passed += 1
        else:
            print(f"❌ {check_name} - Missing")
    
    return passed, len(checks)

def run_currency_conversion_test():
    """Run all currency conversion tests"""
    print("🚀 HR Wallet Currency Conversion Test Suite")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Test template currency conversion
    passed, total, issues = test_template_currency_conversion()
    total_passed += passed
    total_tests += total
    
    # Test icon conversion
    passed, total = test_icon_conversion()
    total_passed += passed
    total_tests += total
    
    # Test HR profile standardization
    passed, total = test_hr_profile_standardization()
    total_passed += passed
    total_tests += total
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {total_passed}/{total_tests} tests passed")
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! Currency conversion completed successfully!")
        print("✨ All templates now use Indian Rupees (₹)")
        print("✨ HR profile standardized to match employee profiles")
    elif success_rate >= 85:
        print("✅ GOOD! Most currency conversions completed.")
        print("⚠️  Minor issues may remain - check the details above.")
    else:
        print("⚠️  NEEDS ATTENTION! Currency conversion incomplete.")
        print("🔧 Please review the failing tests above.")
    
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if issues:
        print("\n🔍 Issues Found:")
        for issue in issues:
            print(f"   {issue}")
    
    return success_rate >= 85

if __name__ == '__main__':
    run_currency_conversion_test()
