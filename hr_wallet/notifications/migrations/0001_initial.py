# Generated manually by Augment Agent
from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(getattr(settings, 'AUTH_USER_MODEL', 'auth.User')),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(default='general', max_length=50)),
                ('is_read', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.CharField(blank=True, max_length=64)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_date']},
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_enabled', models.BooleanField(default=True)),
                ('in_app_enabled', models.BooleanField(default=True)),
                ('notification_types', models.JSONField(blank=True, default=dict)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read', 'created_date'], name='notif_user_read_idx'),
        ),
    ]

