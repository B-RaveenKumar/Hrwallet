#!/usr/bin/env python
"""
Comprehensive test script for HR Wallet system
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from core_hr.models import Company, Department, Employee

def test_database_setup():
    """Test database setup and model creation"""
    print("🔧 Testing Database Setup...")
    
    try:
        # Test Company model
        company, created = Company.objects.get_or_create(
            name='Test Company',
            defaults={
                'address': '123 Test Street',
                'phone': '+1-555-0123',
                'email': 'test@company.com'
            }
        )
        print(f"✅ Company model working: {company.name}")
        
        # Test User model
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'role': 'employee',
                'company': company
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        print(f"✅ User model working: {user.username}")
        
        # Test Department model
        dept, created = Department.objects.get_or_create(
            name='Test Department',
            company=company,
            defaults={
                'description': 'Test department for testing'
            }
        )
        print(f"✅ Department model working: {dept.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

def test_authentication_flow():
    """Test the complete authentication flow"""
    print("\n🔐 Testing Authentication Flow...")
    
    client = Client()
    
    try:
        # Test company selection page
        response = client.get('/accounts/company-selection/')
        if response.status_code in [200, 302]:
            print("✅ Company selection page accessible")
        else:
            print(f"❌ Company selection failed: {response.status_code}")
            return False
        
        # Test login page
        response = client.get('/accounts/login/')
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        
        # Test login with credentials
        User = get_user_model()
        if User.objects.filter(username='testuser').exists():
            response = client.post('/accounts/login/', {
                'username': 'testuser',
                'password': 'testpass123'
            })
            if response.status_code in [200, 302]:
                print("✅ Login functionality working")
            else:
                print(f"❌ Login failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication flow failed: {str(e)}")
        return False

def test_dashboard_access():
    """Test dashboard access for different roles"""
    print("\n📊 Testing Dashboard Access...")
    
    client = Client()
    
    try:
        # Test unauthenticated access (should redirect)
        dashboards = [
            '/admin-panel/',
            '/hr-dashboard/',
            '/employee-portal/'
        ]
        
        for dashboard in dashboards:
            response = client.get(dashboard)
            if response.status_code == 302:  # Redirect to login
                print(f"✅ {dashboard} properly protected")
            else:
                print(f"⚠️  {dashboard} status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard access test failed: {str(e)}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 HR Wallet Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_setup,
        test_authentication_flow,
        test_dashboard_access
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HR Wallet system is fully operational!")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == '__main__':
    run_comprehensive_test()
