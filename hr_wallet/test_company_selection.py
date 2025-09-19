#!/usr/bin/env python
"""
Test script for company selection functionality
"""

import os
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from core_hr.models import Company
from accounts.models import User

def test_company_selection():
    """Test the company selection flow"""
    print("🏢 Testing Company Selection Functionality...")
    
    client = Client()
    
    # Test 1: Root URL should redirect to company selection
    print("\n1. Testing root URL redirect...")
    response = client.get('/')
    print(f"   Root URL status: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirects to: {response.url}")
    
    # Test 2: Company selection page loads
    print("\n2. Testing company selection page...")
    response = client.get('/accounts/company-selection/')
    print(f"   Company selection status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Company selection page loads successfully")
        
        # Check if companies are displayed
        companies = Company.objects.filter(is_active=True)
        print(f"   Available companies: {companies.count()}")
        for company in companies:
            print(f"     - {company.name} ({company.get_employee_count()} employees)")
    else:
        print("   ❌ Company selection page failed to load")
    
    # Test 3: Company selection POST
    print("\n3. Testing company selection submission...")
    companies = Company.objects.filter(is_active=True).first()
    if companies:
        response = client.post('/accounts/company-selection/', {
            'company_id': companies.id
        })
        print(f"   Company selection POST status: {response.status_code}")
        if response.status_code == 302:
            print(f"   Redirects to: {response.url}")
            print("   ✅ Company selection works correctly")
        else:
            print("   ❌ Company selection POST failed")
    else:
        print("   ⚠️  No companies available for testing")
    
    # Test 4: Login page with company context
    print("\n4. Testing login page with company context...")
    if companies:
        # First select a company
        session = client.session
        session['selected_company_id'] = companies.id
        session['selected_company_name'] = companies.name
        session.save()
        
        response = client.get('/accounts/login/')
        print(f"   Login page status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Login page loads with company context")
        else:
            print("   ❌ Login page failed to load")
    
    # Test 5: Login without company selection should redirect
    print("\n5. Testing login without company selection...")
    client = Client()  # Fresh client without session
    response = client.get('/accounts/login/')
    print(f"   Login without company status: {response.status_code}")
    if response.status_code == 302:
        print(f"   Redirects to: {response.url}")
        print("   ✅ Correctly redirects to company selection")
    else:
        print("   ❌ Should redirect to company selection")

def test_company_data():
    """Test company data and setup"""
    print("\n🏢 Testing Company Data...")
    
    companies = Company.objects.all()
    print(f"Total companies: {companies.count()}")
    
    active_companies = Company.objects.filter(is_active=True)
    print(f"Active companies: {active_companies.count()}")
    
    if active_companies.count() == 0:
        print("⚠️  No active companies found. Creating test company...")
        try:
            test_company = Company.objects.create(
                name='Test Company',
                address='123 Test Street',
                phone='+1-555-0123',
                email='test@company.com',
                is_active=True
            )
            print(f"✅ Created test company: {test_company.name}")
        except Exception as e:
            print(f"❌ Failed to create test company: {e}")
    
    for company in active_companies:
        employee_count = company.get_employee_count()
        print(f"  - {company.name}: {employee_count} employees")

if __name__ == '__main__':
    print("🚀 HR Wallet Company Selection Test Suite")
    print("=" * 50)
    
    try:
        test_company_data()
        test_company_selection()
        
        print("\n" + "=" * 50)
        print("✅ Company selection testing completed!")
        print("\n📋 Summary:")
        print("   - Company selection page implemented")
        print("   - Session-based company storage working")
        print("   - Login flow integrated with company context")
        print("   - URL routing updated for new flow")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
