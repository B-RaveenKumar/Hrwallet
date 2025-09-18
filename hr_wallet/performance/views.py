from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from accounts.decorators import require_roles
from .models import Goal, PerformanceReview, Feedback
from core_hr.models import Employee

@login_required
def goals(request):
    if request.user.role in ('super_admin','hr_manager'):
        goals = Goal.objects.select_related('employee__user').order_by('-created_at')
    else:
        emp = getattr(request.user, 'employee', None)
        if not emp:
            return HttpResponseForbidden()
        goals = Goal.objects.filter(employee=emp).order_by('-created_at')
    return render(request, 'performance/goals.html', {'goals': goals})

@login_required
def update_goal_status(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    if request.user.role not in ('super_admin','hr_manager'):
        if getattr(request.user, 'employee', None) != goal.employee:
            return HttpResponseForbidden()
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Goal.STATUS_CHOICES):
            goal.status = status
            goal.save(update_fields=['status'])
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@require_roles('super_admin','hr_manager')
@login_required
def reviews(request):
    reviews = PerformanceReview.objects.select_related('employee__user').order_by('-review_period_end')
    return render(request, 'performance/reviews.html', {'reviews': reviews})

@require_roles('super_admin','hr_manager')
@login_required
def feedback(request):
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        text = request.POST.get('feedback_text')
        ftype = request.POST.get('feedback_type')
        emp = get_object_or_404(Employee, id=emp_id)
        Feedback.objects.create(employee=emp, given_by=request.user, feedback_text=text, feedback_type=ftype)
        return redirect('performance:feedback')
    items = Feedback.objects.select_related('employee__user').order_by('-created_date')
    return render(request, 'performance/feedback.html', {'items': items})

