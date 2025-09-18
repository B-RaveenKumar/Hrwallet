from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core_hr", "0005_remove_company_annual_leave_days_remove_company_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="biometricdevice",
            name="comm_key",
            field=models.PositiveIntegerField(default=0),
        ),
    ]

