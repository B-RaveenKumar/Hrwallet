from django.core.management.base import BaseCommand
from django.utils import timezone
from payroll.models import PaySlip, EmployeeSalary
from core_hr.models import Employee
from datetime import datetime
import calendar

class Command(BaseCommand):
    help = 'Generate payroll for all employees for a specific month and auto-generate PDFs'

    def add_arguments(self, parser):
        parser.add_argument('--month', type=str, required=True, 
                          help='Month in YYYY-MM format (e.g., 2024-01)')
        parser.add_argument('--generate-pdf', action='store_true', 
                          help='Generate PDF files for all payslips')

    def handle(self, *args, **options):
        month_str = options['month']
        generate_pdf = options.get('generate_pdf', False)
        
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid month format. Use YYYY-MM'))
            return

        # Get first and last day of the month
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

        employees = Employee.objects.filter(is_active=True)
        created_count = 0
        pdf_count = 0

        for employee in employees:
            # Check if payslip already exists
            if PaySlip.objects.filter(employee=employee, 
                                    pay_period_start=first_day, 
                                    pay_period_end=last_day).exists():
                self.stdout.write(f'Payslip already exists for {employee.user.get_full_name()}')
                continue

            # Get employee salary
            try:
                salary = EmployeeSalary.objects.filter(employee=employee).latest('effective_date')
            except EmployeeSalary.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'No salary record for {employee.user.get_full_name()}'))
                continue

            # Create payslip
            payslip = PaySlip.objects.create(
                employee=employee,
                pay_period_start=first_day,
                pay_period_end=last_day
            )
            
            # Calculate amounts
            payslip.calculate_amounts()
            created_count += 1
            
            # Generate PDF if requested
            if generate_pdf:
                pdf_path = payslip.generate_pdf()
                if pdf_path:
                    pdf_count += 1
                    self.stdout.write(f'Generated PDF for {employee.user.get_full_name()}: {pdf_path}')
                else:
                    self.stdout.write(self.style.WARNING(f'Failed to generate PDF for {employee.user.get_full_name()}'))
            
            self.stdout.write(f'Created payslip for {employee.user.get_full_name()}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} payslips for {month_str}')
        )
        
        if generate_pdf:
            self.stdout.write(
                self.style.SUCCESS(f'Generated {pdf_count} PDF files')
            )
