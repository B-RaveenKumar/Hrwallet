from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from decimal import Decimal
import random

from core_hr.models import Company, Department, Employee, Attendance, LeaveRequest, Payroll, LeaveBalance, WorkHours
from accounts.models import User


class Command(BaseCommand):
    help = 'DEPRECATED: This command is deprecated. Use setup_demo_company instead.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run the deprecated command',
        )

    def handle(self, *args, **options):
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    'This command is deprecated and has been replaced with dynamic company setup.\n'
                    'Use the following commands instead:\n'
                    '  python manage.py setup_demo_company\n'
                    '  python manage.py create_company\n'
                    '\nTo run this deprecated command anyway, use --force flag.'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Starting to populate live data...'))

        # Get all employees
        employees = Employee.objects.all()

        if not employees.exists():
            self.stdout.write(self.style.ERROR('No employees found. Please create a company and users first.'))
            return
        
        # Create leave balances for all employees
        self.create_leave_balances(employees)
        
        # Create attendance records for the last 30 days
        self.create_attendance_records(employees)
        
        # Create work hours records
        self.create_work_hours(employees)
        
        # Create payroll records
        self.create_payroll_records(employees)
        
        # Create some leave requests
        self.create_leave_requests(employees)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated live data!'))

    def create_leave_balances(self, employees):
        self.stdout.write('Creating leave balances...')
        
        for employee in employees:
            leave_balance, created = LeaveBalance.objects.get_or_create(
                employee=employee,
                defaults={
                    'annual_leave_total': random.randint(18, 25),
                    'annual_leave_used': random.randint(0, 8),
                    'sick_leave_total': random.randint(8, 12),
                    'sick_leave_used': random.randint(0, 4),
                    'personal_leave_total': random.randint(3, 7),
                    'personal_leave_used': random.randint(0, 2),
                }
            )
            if created:
                self.stdout.write(f'  Created leave balance for {employee.user.username}')

    def create_attendance_records(self, employees):
        self.stdout.write('Creating attendance records...')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        for employee in employees:
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                    # 90% chance of being present
                    if random.random() < 0.9:
                        status = 'present'
                        # 10% chance of being late if present
                        if random.random() < 0.1:
                            status = 'late'
                            clock_in_hour = random.randint(9, 10)
                            clock_in_minute = random.randint(15, 59)
                        else:
                            clock_in_hour = random.randint(8, 9)
                            clock_in_minute = random.randint(0, 30)
                        
                        clock_in = time(clock_in_hour, clock_in_minute)
                        
                        # Clock out time (8-9 hours later)
                        work_hours = random.uniform(7.5, 9.0)
                        clock_out_time = datetime.combine(current_date, clock_in) + timedelta(hours=work_hours)
                        clock_out = clock_out_time.time()
                        
                        total_hours = Decimal(str(round(work_hours, 2)))
                    else:
                        status = 'absent'
                        clock_in = None
                        clock_out = None
                        total_hours = Decimal('0.00')
                    
                    attendance, created = Attendance.objects.get_or_create(
                        employee=employee,
                        date=current_date,
                        defaults={
                            'clock_in': clock_in,
                            'clock_out': clock_out,
                            'total_hours': total_hours,
                            'status': status,
                        }
                    )
                
                current_date += timedelta(days=1)
        
        self.stdout.write(f'  Created attendance records for {employees.count()} employees')

    def create_work_hours(self, employees):
        self.stdout.write('Creating work hours records...')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        for employee in employees:
            attendance_records = Attendance.objects.filter(
                employee=employee,
                date__gte=start_date,
                date__lte=end_date,
                status__in=['present', 'late']
            )
            
            for attendance in attendance_records:
                if attendance.total_hours:
                    regular_hours = min(attendance.total_hours, Decimal('8.0'))
                    overtime_hours = max(Decimal('0.0'), attendance.total_hours - Decimal('8.0'))
                    
                    WorkHours.objects.get_or_create(
                        employee=employee,
                        date=attendance.date,
                        defaults={
                            'regular_hours': regular_hours,
                            'overtime_hours': overtime_hours,
                            'break_hours': Decimal('1.0'),  # Standard 1-hour break
                        }
                    )
        
        self.stdout.write(f'  Created work hours records for {employees.count()} employees')

    def create_payroll_records(self, employees):
        self.stdout.write('Creating payroll records...')
        
        # Create payroll for last 3 months
        current_date = timezone.now().date()
        
        for i in range(3):
            # Calculate pay period (monthly)
            if i == 0:
                # Current month
                pay_period_end = current_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
            else:
                pay_period_end = (current_date.replace(day=1) - timedelta(days=i*30)).replace(day=1) - timedelta(days=1)
            
            pay_period_start = pay_period_end.replace(day=1)
            
            for employee in employees:
                if employee.salary:
                    basic_salary = employee.salary
                    allowances = basic_salary * Decimal('0.1')  # 10% allowances
                    overtime_pay = Decimal(str(random.uniform(0, 500)))  # Random overtime
                    
                    # Deductions
                    tax_rate = Decimal('0.15')  # 15% tax
                    insurance = Decimal('200')  # Fixed insurance
                    
                    payroll, created = Payroll.objects.get_or_create(
                        employee=employee,
                        pay_period_start=pay_period_start,
                        pay_period_end=pay_period_end,
                        defaults={
                            'basic_salary': basic_salary,
                            'allowances': allowances,
                            'overtime_pay': overtime_pay,
                            'tax_deduction': (basic_salary + allowances + overtime_pay) * tax_rate,
                            'insurance_deduction': insurance,
                            'other_deductions': Decimal('50'),  # Other deductions
                            'status': 'paid' if i > 0 else 'processed',
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  Created payroll for {employee.user.username} - {pay_period_start} to {pay_period_end}')

    def create_leave_requests(self, employees):
        self.stdout.write('Creating leave requests...')
        
        leave_types = ['annual', 'sick', 'personal', 'emergency']
        statuses = ['pending', 'approved', 'rejected']
        
        for employee in employees:
            # Create 2-5 leave requests per employee
            num_requests = random.randint(2, 5)
            
            for _ in range(num_requests):
                leave_type = random.choice(leave_types)
                
                # Random date in the past 60 days or future 30 days
                base_date = timezone.now().date()
                start_date = base_date + timedelta(days=random.randint(-60, 30))
                days_requested = random.randint(1, 5)
                end_date = start_date + timedelta(days=days_requested - 1)
                
                # Status based on date (past requests are more likely to be approved/rejected)
                if start_date < base_date:
                    status = random.choice(['approved', 'rejected'])
                else:
                    status = random.choice(['pending', 'approved'])
                
                reasons = [
                    'Family vacation',
                    'Medical appointment',
                    'Personal matters',
                    'Emergency situation',
                    'Wedding ceremony',
                    'Moving house',
                    'Child care',
                ]
                
                LeaveRequest.objects.get_or_create(
                    employee=employee,
                    start_date=start_date,
                    end_date=end_date,
                    defaults={
                        'leave_type': leave_type,
                        'days_requested': days_requested,
                        'reason': random.choice(reasons),
                        'status': status,
                    }
                )
        
        self.stdout.write(f'  Created leave requests for {employees.count()} employees')
