#!/usr/bin/env python
"""
Create demo companies for testing the company selection functionality
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_wallet.settings')
django.setup()

from core_hr.models import Company

def create_demo_companies():
    """Create demo companies for testing"""
    print("🏢 Creating Demo Companies...")
    
    demo_companies = [
        {
            'name': 'TechCorp Solutions',
            'address': '123 Innovation Drive, Tech City, TC 12345',
            'phone': '+1-555-0100',
            'email': 'info@techcorp.com',
            'website': 'https://techcorp.com',
            'subscription_plan': 'premium',
            'max_employees': 500,
            'slug': 'techcorp-solutions',
        },
        {
            'name': 'Global Manufacturing Inc',
            'address': '456 Industrial Blvd, Factory Town, FT 67890',
            'phone': '+1-555-0200',
            'email': 'contact@globalmanuf.com',
            'website': 'https://globalmanuf.com',
            'subscription_plan': 'enterprise',
            'max_employees': 1000,
            'slug': 'global-manufacturing-inc',
        },
        {
            'name': 'Creative Design Studio',
            'address': '789 Art Street, Design District, DD 11111',
            'phone': '+1-555-0300',
            'email': 'hello@creativedesign.com',
            'website': 'https://creativedesign.com',
            'subscription_plan': 'basic',
            'max_employees': 50,
            'slug': 'creative-design-studio',
        },
        {
            'name': 'Healthcare Partners',
            'address': '321 Medical Center Dr, Health City, HC 22222',
            'phone': '+1-555-0400',
            'email': 'admin@healthpartners.com',
            'website': 'https://healthpartners.com',
            'subscription_plan': 'premium',
            'max_employees': 200,
            'slug': 'healthcare-partners',
        },
        {
            'name': 'Financial Services Group',
            'address': '654 Banking Plaza, Finance District, FD 33333',
            'phone': '+1-555-0500',
            'email': 'info@finservices.com',
            'website': 'https://finservices.com',
            'subscription_plan': 'enterprise',
            'max_employees': 800,
            'slug': 'financial-services-group',
        }
    ]
    
    created_count = 0
    
    for company_data in demo_companies:
        try:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults=company_data
            )
            
            if created:
                print(f"✅ Created: {company.name}")
                created_count += 1
            else:
                print(f"⚠️  Already exists: {company.name}")
                
        except Exception as e:
            print(f"❌ Failed to create {company_data['name']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   - {created_count} new companies created")
    print(f"   - {Company.objects.count()} total companies in system")
    print(f"   - {Company.objects.filter(is_active=True).count()} active companies")
    
    # List all companies
    print(f"\n🏢 All Companies:")
    for company in Company.objects.all().order_by('name'):
        status = "✅ Active" if company.is_active else "❌ Inactive"
        print(f"   - {company.name} ({status})")
        print(f"     📧 {company.email} | 📞 {company.phone}")
        print(f"     🌐 {company.website} | 📋 {company.subscription_plan}")
        print(f"     👥 Max employees: {company.max_employees}")
        print()

if __name__ == '__main__':
    print("🚀 HR Wallet Demo Company Creator")
    print("=" * 50)
    
    try:
        create_demo_companies()
        print("=" * 50)
        print("✅ Demo companies creation completed!")
        
    except Exception as e:
        print(f"\n❌ Failed with error: {e}")
        import traceback
        traceback.print_exc()
