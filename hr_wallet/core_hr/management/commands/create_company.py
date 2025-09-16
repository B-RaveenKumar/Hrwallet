from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date

from core_hr.models import Company, Department
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a new company in the HR Wallet system'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Company name')
        parser.add_argument('--code', type=str, required=True, help='Company code (short identifier)')
        parser.add_argument('--address', type=str, help='Company address')
        parser.add_argument('--phone', type=str, help='Company phone number')
        parser.add_argument('--email', type=str, help='Company email address')
        parser.add_argument('--website', type=str, help='Company website URL')
        parser.add_argument('--admin-username', type=str, help='Create admin user with this username')
        parser.add_argument('--admin-email', type=str, help='Admin user email')
        parser.add_argument('--admin-password', type=str, help='Admin user password')

    def handle(self, *args, **options):
        name = options['name']
        code = options['code'].upper()
        
        self.stdout.write(self.style.SUCCESS(f'Creating company: {name} ({code})'))
        
        try:
            with transaction.atomic():
                # Create company
                company = Company.objects.create(
                    name=name,
                    code=code,
                    address=options.get('address', f'{name} Headquarters'),
                    phone=options.get('phone', '+1-555-0000'),
                    email=options.get('email', f'info@{code.lower()}.com'),
                    website=options.get('website', f'https://www.{code.lower()}.com'),
                    established_date=date.today(),
                    is_active=True,
                )
                
                self.stdout.write(f'  ✓ Created company: {company.name}')
                
                # Create default departments
                default_departments = [
                    'Human Resources',
                    'Information Technology', 
                    'Finance',
                    'Operations',
                ]
                
                for dept_name in default_departments:
                    department = Department.objects.create(
                        company=company,
                        name=dept_name,
                        description=f'{dept_name} department'
                    )
                    self.stdout.write(f'  ✓ Created department: {department.name}')
                
                # Create admin user if requested
                admin_username = options.get('admin_username')
                if admin_username:
                    admin_email = options.get('admin_email', f'admin@{code.lower()}.com')
                    admin_password = options.get('admin_password', 'admin123')
                    
                    admin_user = User.objects.create_user(
                        username=admin_username,
                        email=admin_email,
                        first_name='System',
                        last_name='Administrator',
                        password=admin_password,
                        role='super_admin',
                        company=company,
                        is_active=True,
                    )
                    
                    self.stdout.write(f'  ✓ Created admin user: {admin_user.username}')
                    self.stdout.write(f'    Email: {admin_user.email}')
                    self.stdout.write(f'    Password: {admin_password}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ Company setup completed successfully!\n'
                        f'Company: {company.name} ({company.code})\n'
                        f'Departments: {len(default_departments)}\n'
                        f'Access URL: http://127.0.0.1:8000/\n'
                        f'Select "{company.name}" from the company selection page.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating company: {str(e)}'))
            raise
