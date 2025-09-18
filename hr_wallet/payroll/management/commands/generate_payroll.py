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
        with transaction.atomic():
            for emp in Employee.objects.filter(is_active=True):
                sal = EmployeeSalary.objects.filter(employee=emp, is_active=True).order_by('-effective_date').first()
                if not sal:
                    continue
                slip, created = PaySlip.objects.get_or_create(
                    employee=emp, pay_period_start=start, pay_period_end=end,
                )
                slip.calculate_totals(sal)
                slip.save()
                slip.generate_pdf()
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Payroll generated for {count} employees for {options["month"]}'))

