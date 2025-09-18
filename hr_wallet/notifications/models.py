from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default='general')
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        indexes = [models.Index(fields=['user', 'is_read', 'created_date'])]
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Send real-time notification if new and user has in-app notifications enabled
        if is_new:
            try:
                pref = getattr(self.user, 'notificationpreference', None)
                if not pref or pref.in_app_enabled:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'notifications_{self.user.id}',
                        {
                            'type': 'notification_message',
                            'message': {
                                'id': self.id,
                                'title': self.title,
                                'message': self.message,
                                'notification_type': self.notification_type,
                                'created_date': self.created_date.isoformat(),
                            }
                        }
                    )
            except Exception:
                # Fail silently if channels not available
                pass

class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    notification_types = models.JSONField(default=dict, blank=True)

