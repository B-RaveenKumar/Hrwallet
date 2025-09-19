from datetime import date
from calendar import monthrange
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core_hr.models import Employee
from payroll.models import EmployeeSalary, PaySlip

class Command(BaseCommand):
    help = 'Generate payroll for all active employees for a given month (YYYY-MM)'

    def add_arguments(self, parser):
        parser.add_argument('--month', required=True, help='Format: YYYY-MM')

    def handle(self, *args, **options):
        year, mon = map(int, options['month'].split('-'))
        start = date(year, mon, 1)
        end = date(year, mon, monthrange(year, mon)[1])
        count = 0
        skipped = 0
        errors = 0

        self.stdout.write(f'Generating payroll for {options["month"]}...')

        with transaction.atomic():
            for emp in Employee.objects.filter(is_active=True):
                try:
                    # Get the active salary record for the employee
                    sal = EmployeeSalary.objects.filter(
                        employee=emp,
                        is_active=True,
                        status='approved',
                        effective_date__lte=end  # Salary must be effective by the end of the period
                    ).order_by('-effective_date').first()

                    if not sal:
                        self.stdout.write(
                            self.style.WARNING(f'No active salary found for {emp.user.get_full_name()} ({emp.employee_id})')
                        )
                        skipped += 1
                        continue

                    # Check if payslip already exists
                    slip, created = PaySlip.objects.get_or_create(
                        employee=emp,
                        pay_period_start=start,
                        pay_period_end=end,
                    )

                    if created:
                        self.stdout.write(f'Creating new payslip for {emp.user.get_full_name()}')
                    else:
                        self.stdout.write(f'Updating existing payslip for {emp.user.get_full_name()}')

                    # Calculate payslip amounts using the salary record
                    slip.calculate_totals(sal)
                    slip.save()

                    # Generate PDF
                    pdf_path = slip.generate_pdf()
                    if pdf_path:
                        self.stdout.write(f'Generated PDF: {pdf_path}')

                    count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing {emp.user.get_full_name()}: {str(e)}')
                    )
                    errors += 1
                    continue

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'Payroll generation completed for {options["month"]}:\n'
            f'  - Successfully processed: {count} employees\n'
            f'  - Skipped (no salary): {skipped} employees\n'
            f'  - Errors: {errors} employees'
        ))

