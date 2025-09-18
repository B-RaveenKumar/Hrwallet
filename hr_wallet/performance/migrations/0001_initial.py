# Generated manually by Augment Agent
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('core_hr', '0006_add_biometricdevice_comm_key'),
        migrations.swappable_dependency(getattr(settings, 'AUTH_USER_MODEL', 'auth.User')),
    ]

    operations = [
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('target_date', models.DateField()),
                ('status', models.CharField(choices=[('pending','Pending'),('in_progress','In Progress'),('completed','Completed'),('overdue','Overdue')], default='pending', max_length=20)),
                ('priority', models.CharField(choices=[('low','Low'),('medium','Medium'),('high','High')], default='medium', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core_hr.employee')),
            ],
        ),
        migrations.CreateModel(
            name='PerformanceReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_period_start', models.DateField()),
                ('review_period_end', models.DateField()),
                ('self_evaluation_score', models.IntegerField(blank=True, null=True)),
                ('manager_evaluation_score', models.IntegerField(blank=True, null=True)),
                ('overall_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('status', models.CharField(choices=[('draft','Draft'),('submitted','Submitted'),('reviewed','Reviewed'),('closed','Closed')], default='draft', max_length=20)),
                ('comments', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core_hr.employee')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_text', models.TextField()),
                ('feedback_type', models.CharField(choices=[('positive','Positive'),('constructive','Constructive'),('general','General')], default='general', max_length=20)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core_hr.employee')),
                ('given_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

