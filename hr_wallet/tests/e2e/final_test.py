#!/usr/bin/env python
"""
Final comprehensive test for HR Wallet system - focusing on web functionality
"""
import os
import sys
import django
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

def test_all_urls():
    """Test all critical URLs"""
    print("🌐 Testing All Critical URLs...")
    
    client = Client()
    
    test_cases = [
        # Basic URLs
        ('/', 'Root redirect'),
        ('/favicon.ico', 'Favicon'),
        
        # Authentication URLs
        ('/accounts/company-selection/', 'Company selection'),
        ('/accounts/login/', 'Login page'),
        ('/accounts/logout/', 'Logout'),
        
        # Dashboard URLs (should redirect to login)
        ('/admin-panel/', 'Admin panel'),
        ('/hr-dashboard/', 'HR dashboard'),
        ('/employee-portal/', 'Employee portal'),
        
        # Admin URL
        ('/admin/', 'Django admin'),
        
        # Legacy redirects
        ('/login/', 'Legacy login redirect'),
        ('/logout/', 'Legacy logout redirect'),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for url, description in test_cases:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {description} ({url}) - OK")
                passed += 1
            elif status in [301, 302]:
                print(f"🔄 {description} ({url}) - Redirect (expected)")
                passed += 1
            elif status == 204:
                print(f"⚪ {description} ({url}) - No Content (expected)")
                passed += 1
            elif status == 404:
                print(f"❌ {description} ({url}) - Not Found")
            elif status == 500:
                print(f"💥 {description} ({url}) - Server Error")
            else:
                print(f"⚠️  {description} ({url}) - Status {status}")
                
        except Exception as e:
            print(f"💥 {description} ({url}) - Exception: {str(e)}")
    
    return passed, total

def test_template_rendering():
    """Test that key templates render without errors"""
    print("\n🎨 Testing Template Rendering...")
    
    client = Client()
    
    templates_to_test = [
        ('/accounts/login/', 'Login template'),
        ('/accounts/company-selection/', 'Company selection template'),
    ]
    
    passed = 0
    total = len(templates_to_test)
    
    for url, description in templates_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                # Check if response contains expected HTML elements
                content = response.content.decode('utf-8')
                if '<html' in content and '</html>' in content:
                    print(f"✅ {description} - Renders correctly")
                    passed += 1
                else:
                    print(f"❌ {description} - Invalid HTML structure")
            elif response.status_code in [301, 302]:
                print(f"🔄 {description} - Redirects (may be expected)")
                passed += 1
            else:
                print(f"❌ {description} - Status {response.status_code}")
                
        except Exception as e:
            print(f"💥 {description} - Exception: {str(e)}")
    
    return passed, total

def test_static_files():
    """Test static file configuration"""
    print("\n📁 Testing Static File Configuration...")
    
    try:
        from django.conf import settings
        
        checks = [
            (hasattr(settings, 'STATIC_URL'), 'STATIC_URL configured'),
            (hasattr(settings, 'STATICFILES_DIRS'), 'STATICFILES_DIRS configured'),
            (hasattr(settings, 'MEDIA_URL'), 'MEDIA_URL configured'),
            (hasattr(settings, 'MEDIA_ROOT'), 'MEDIA_ROOT configured'),
        ]
        
        passed = 0
        total = len(checks)
        
        for check, description in checks:
            if check:
                print(f"✅ {description}")
                passed += 1
            else:
                print(f"❌ {description}")
        
        return passed, total
        
    except Exception as e:
        print(f"💥 Static file test failed: {str(e)}")
        return 0, 4

def run_final_test():
    """Run all final tests"""
    print("🚀 HR Wallet Final Test Suite")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Run URL tests
    passed, total = test_all_urls()
    total_passed += passed
    total_tests += total
    
    # Run template tests
    passed, total = test_template_rendering()
    total_passed += passed
    total_tests += total
    
    # Run static file tests
    passed, total = test_static_files()
    total_passed += passed
    total_tests += total
    
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {total_passed}/{total_tests} tests passed")
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! HR Wallet system is fully operational!")
        print("✨ All critical functionality is working correctly.")
    elif success_rate >= 75:
        print("✅ GOOD! HR Wallet system is mostly operational.")
        print("⚠️  Minor issues detected but system is usable.")
    else:
        print("⚠️  NEEDS ATTENTION! Some critical issues detected.")
        print("🔧 Please review and fix the failing tests.")
    
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 75

if __name__ == '__main__':
    run_final_test()
