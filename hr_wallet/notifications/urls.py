from django.urls import path
from . import views
app_name = 'notifications'

urlpatterns = [
    path('api/unread/', views.unread, name='api_unread'),
    path('api/mark-read/<int:pk>/', views.mark_read, name='api_mark_read'),
    path('settings/', views.preferences, name='settings'),
]

