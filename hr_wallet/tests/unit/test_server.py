#!/usr/bin/env python
"""
Simple test script to check if the HR Wallet server is working
"""
import os
import sys
import django
from django.test import Client
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

def test_urls():
    """Test critical URLs"""
    client = Client()
    
    test_urls = [
        '/',
        '/accounts/company-selection/',
        '/accounts/login/',
        '/favicon.ico',
        '/admin-panel/',
        '/hr-dashboard/',
        '/employee-portal/',
        '/admin/',
    ]
    
    print("Testing HR Wallet URLs...")
    print("=" * 50)
    
    for url in test_urls:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {url} - OK (200)")
            elif status in [301, 302]:
                print(f"🔄 {url} - Redirect ({status})")
            elif status == 404:
                print(f"❌ {url} - Not Found (404)")
            elif status == 500:
                print(f"💥 {url} - Server Error (500)")
            else:
                print(f"⚠️  {url} - Status {status}")
                
        except Exception as e:
            print(f"💥 {url} - Exception: {str(e)}")
    
    print("=" * 50)
    print("Test completed!")

if __name__ == '__main__':
    test_urls()
