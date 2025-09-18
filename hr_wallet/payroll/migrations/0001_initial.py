# Generated manually by Augment Agent
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('core_hr', '0006_add_biometricdevice_comm_key'),
        migrations.swappable_dependency(getattr(settings, 'AUTH_USER_MODEL', 'auth.User')),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxBracket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('income_min', models.DecimalField(decimal_places=2, max_digits=12)),
                ('income_max', models.DecimalField(decimal_places=2, max_digits=12)),
                ('tax_rate', models.DecimalField(decimal_places=2, help_text='Percent rate, e.g. 10.00 for 10%', max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['income_min']},
        ),
        migrations.CreateModel(
            name='DeductionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_percentage', models.BooleanField(default=False)),
                ('amount_or_percentage', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='EmployeeSalary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basic_salary', models.DecimalField(decimal_places=2, max_digits=12)),
                ('allowances', models.JSONField(blank=True, default=dict)),
                ('effective_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core_hr.employee')),
            ],
            options={'ordering': ['-effective_date']},
        ),
        migrations.CreateModel(
            name='PaySlip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pay_period_start', models.DateField()),
                ('pay_period_end', models.DateField()),
                ('gross_pay', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_deductions', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('net_pay', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('generated_date', models.DateTimeField(auto_now_add=True)),
                ('pdf_file_path', models.CharField(blank=True, default='', max_length=255)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core_hr.employee')),
            ],
            options={'ordering': ['-pay_period_end']},
        ),
        migrations.AddIndex(
            model_name='employeesalary',
            index=models.Index(fields=['is_active', 'effective_date'], name='payroll_empl_is_acti_ef1b48_idx'),
        ),
        migrations.AddIndex(
            model_name='payslip',
            index=models.Index(fields=['employee', 'pay_period_end'], name='payroll_pays_employ_6b9c88_idx'),
        ),
        migrations.AddIndex(
            model_name='taxbracket',
            index=models.Index(fields=['is_active', 'income_min', 'income_max'], name='payroll_taxb_is_acti_1a415a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='payslip',
            unique_together={('employee', 'pay_period_start', 'pay_period_end')},
        ),
    ]

