from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta, date, time
from decimal import Decimal
import random

from core_hr.models import Company, Department, Employee, Attendance, LeaveRequest, Payroll, LeaveBalance, WorkHours
from accounts.models import User


class Command(BaseCommand):
    help = 'Setup a demo company with sample data for testing the HR Wallet system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            default='Demo Tech Solutions',
            help='Name of the demo company to create',
        )
        parser.add_argument(
            '--company-code',
            type=str,
            default='DEMO',
            help='Short code for the demo company',
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip creating demo users (only create company structure)',
        )

    def handle(self, *args, **options):
        company_name = options['company_name']
        company_code = options['company_code']
        skip_users = options['skip_users']
        
        self.stdout.write(self.style.SUCCESS(f'Setting up demo company: {company_name}'))
        
        try:
            with transaction.atomic():
                # Create demo company
                company = self.create_company(company_name, company_code)
                
                # Create departments
                departments = self.create_departments(company)
                
                if not skip_users:
                    # Create demo users and employees
                    users = self.create_demo_users(company, departments)
                    
                    # Create sample data
                    self.create_sample_data(users)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created demo company: {company.name}\n'
                        f'Company Code: {company.code}\n'
                        f'Departments: {len(departments)}\n'
                        f'Access the system at: http://127.0.0.1:8000/\n'
                        f'Select "{company.name}" and use the demo credentials.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up demo company: {str(e)}'))
            raise

    def create_company(self, name, code):
        """Create a demo company"""
        company, created = Company.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'address': '123 Business Street, Tech City, TC 12345',
                'phone': '+1-555-0123',
                'email': f'info@{code.lower()}.com',
                'website': f'https://www.{code.lower()}.com',
                'tax_id': f'TAX-{code}-001',
                'registration_number': f'REG-{code}-2024',
                'established_date': date(2020, 1, 1),
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f'  Created company: {company.name}')
        else:
            self.stdout.write(f'  Company already exists: {company.name}')
        
        return company

    def create_departments(self, company):
        """Create demo departments"""
        departments_data = [
            {'name': 'Human Resources', 'description': 'HR and employee management'},
            {'name': 'Information Technology', 'description': 'IT support and development'},
            {'name': 'Finance', 'description': 'Financial planning and accounting'},
            {'name': 'Marketing', 'description': 'Marketing and communications'},
            {'name': 'Operations', 'description': 'Business operations and logistics'},
        ]
        
        departments = []
        for dept_data in departments_data:
            department, created = Department.objects.get_or_create(
                company=company,
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            departments.append(department)
            
            if created:
                self.stdout.write(f'  Created department: {department.name}')
        
        return departments

    def create_demo_users(self, company, departments):
        """Create demo users with different roles"""
        users_data = [
            {
                'username': 'admin',
                'email': f'admin@{company.code.lower()}.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'super_admin',
                'password': 'admin123',
            },
            {
                'username': 'hr.manager',
                'email': f'hr@{company.code.lower()}.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'hr_manager',
                'password': 'password123',
                'department': 'Human Resources',
                'job_title': 'HR Manager',
            },
            {
                'username': 'john.doe',
                'email': f'john.doe@{company.code.lower()}.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'employee',
                'password': 'password123',
                'department': 'Information Technology',
                'job_title': 'Software Developer',
            },
            {
                'username': 'jane.smith',
                'email': f'jane.smith@{company.code.lower()}.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'employee',
                'password': 'password123',
                'department': 'Marketing',
                'job_title': 'Marketing Specialist',
            },
        ]
        
        created_users = []
        for user_data in users_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'company': company,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'  Created user: {user.username} ({user.get_role_display()})')
            
            # Create employee profile if needed
            if user_data['role'] in ['employee', 'hr_manager'] and 'department' in user_data:
                department = next((d for d in departments if d.name == user_data['department']), departments[0])
                
                employee, emp_created = Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'company': company,
                        'employee_id': f"{company.code}{user.id:04d}",
                        'department': department,
                        'job_title': user_data.get('job_title', 'Employee'),
                        'hire_date': timezone.now().date() - timedelta(days=random.randint(30, 365)),
                        'salary': Decimal(str(random.randint(50000, 120000))),
                        'is_active': True,
                    }
                )
                
                if emp_created:
                    self.stdout.write(f'    Created employee profile: {employee.employee_id}')
            
            created_users.append(user)
        
        return created_users

    def create_sample_data(self, users):
        """Create sample attendance, leave, and payroll data"""
        employees = [user.employee for user in users if hasattr(user, 'employee')]
        
        if not employees:
            return
        
        self.stdout.write('  Creating sample data...')
        
        # Create leave balances
        for employee in employees:
            LeaveBalance.objects.get_or_create(
                employee=employee,
                defaults={
                    'annual_leave_total': 21,
                    'annual_leave_used': random.randint(0, 5),
                    'sick_leave_total': 10,
                    'sick_leave_used': random.randint(0, 2),
                    'personal_leave_total': 5,
                    'personal_leave_used': random.randint(0, 1),
                }
            )
        
        # Create recent attendance (last 7 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        for employee in employees:
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() < 5:  # Weekdays only
                    Attendance.objects.get_or_create(
                        employee=employee,
                        date=current_date,
                        defaults={
                            'clock_in': time(9, 0),
                            'clock_out': time(17, 30),
                            'total_hours': Decimal('8.5'),
                            'status': 'present',
                        }
                    )
                current_date += timedelta(days=1)
        
        self.stdout.write('    Sample data created successfully')
