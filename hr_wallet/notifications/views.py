from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification, NotificationPreference

@login_required
def unread(request):
    items = Notification.objects.filter(user=request.user, is_read=False)[:20]
    data = [{'id': n.id, 'title': n.title, 'message': n.message, 't': n.notification_type, 'ts': n.created_date.isoformat()} for n in items]
    return JsonResponse({'success': True, 'data': data})

@login_required
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return JsonResponse({'success': True})

@login_required
def preferences(request):
    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        pref.email_enabled = bool(request.POST.get('email_enabled'))
        pref.in_app_enabled = bool(request.POST.get('in_app_enabled'))
        pref.save()
        return redirect('notifications:settings')
    template = 'notifications/settings.html'
    if getattr(request.user, 'role', '') == 'employee':
        template = 'notifications/settings_employee.html'
    return render(request, template, {'pref': pref})

