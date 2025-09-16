from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date
import random

from core_hr.models import Company, Department, Employee
from accounts.models import User


class Command(BaseCommand):
    help = 'Setup working demo with existing database structure'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up working demo...'))
        
        try:
            with transaction.atomic():
                # Create or get demo company
                company, created = Company.objects.get_or_create(
                    name='Demo Tech Solutions',
                    defaults={
                        'address': '123 Business Street, Tech City, TC 12345',
                        'phone': '+1-555-0123',
                        'email': 'info@demo.com',
                        'website': 'https://www.demo.com',
                        'logo': None,
                    }
                )
                
                if created:
                    self.stdout.write('  ✓ Created Demo Tech Solutions company')
                else:
                    self.stdout.write('  ✓ Demo Tech Solutions company already exists')
                
                # Create departments
                dept_names = ['Human Resources', 'Information Technology', 'Finance', 'Marketing']
                departments = []
                
                for dept_name in dept_names:
                    dept, created = Department.objects.get_or_create(
                        name=dept_name,
                        defaults={'description': f'{dept_name} department'}
                    )
                    departments.append(dept)
                    if created:
                        self.stdout.write(f'  ✓ Created {dept_name} department')
                
                # Create demo users
                demo_users = [
                    {
                        'username': 'admin',
                        'email': 'admin@demo.com',
                        'first_name': 'System',
                        'last_name': 'Administrator',
                        'role': 'super_admin',
                        'password': 'admin123',
                    },
                    {
                        'username': 'hr.manager',
                        'email': 'hr@demo.com',
                        'first_name': 'Sarah',
                        'last_name': 'Johnson',
                        'role': 'hr_manager',
                        'password': 'password123',
                        'department': 'Human Resources',
                        'job_title': 'HR Manager',
                    },
                    {
                        'username': 'john.doe',
                        'email': 'john.doe@demo.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'role': 'employee',
                        'password': 'password123',
                        'department': 'Information Technology',
                        'job_title': 'Software Developer',
                    },
                ]
                
                for user_data in demo_users:
                    user, created = User.objects.get_or_create(
                        username=user_data['username'],
                        defaults={
                            'email': user_data['email'],
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'role': user_data['role'],
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        user.set_password(user_data['password'])
                        user.save()
                        self.stdout.write(f'  ✓ Created user: {user.username} ({user.get_role_display()})')
                    
                    # Create employee profile if needed
                    if user_data['role'] in ['employee', 'hr_manager'] and 'department' in user_data:
                        dept = next((d for d in departments if d.name == user_data['department']), departments[0])
                        
                        employee, emp_created = Employee.objects.get_or_create(
                            user=user,
                            defaults={
                                'employee_id': f"DEMO{user.id:04d}",
                                'department': dept,
                                'job_title': user_data.get('job_title', 'Employee'),
                                'hire_date': date.today(),
                                'salary': random.randint(50000, 120000),
                                'is_active': True,
                            }
                        )
                        
                        if emp_created:
                            self.stdout.write(f'    ✓ Created employee profile: {employee.employee_id}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n🎉 Working demo setup completed!\n\n'
                        '🌐 Access your system:\n'
                        '  URL: http://127.0.0.1:8000/\n'
                        '  Select "Demo Tech Solutions" from company selection\n\n'
                        '👤 Demo Credentials:\n'
                        '  Super Admin: admin / admin123\n'
                        '  HR Manager: hr.manager / password123\n'
                        '  Employee: john.doe / password123\n\n'
                        '🚀 Start server: python manage.py runserver'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up demo: {str(e)}'))
            raise
