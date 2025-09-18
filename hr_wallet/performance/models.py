from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from core_hr.models import Employee

class Goal(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('in_progress','In Progress'),('completed','Completed'),('overdue','Overdue')]
    PRIORITY_CHOICES = [('low','Low'),('medium','Medium'),('high','High')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.target_date < timezone.now().date():
            # allow overdue only if explicitly set
            if self.status not in ('overdue','completed'):
                raise ValidationError('Target date cannot be in the past unless marking overdue/completed.')
        if len(self.title.strip().split()) < 2:
            raise ValidationError('Title should be specific (SMART).')

class PerformanceReview(models.Model):
    STATUS_CHOICES = [('draft','Draft'),('submitted','Submitted'),('reviewed','Reviewed'),('closed','Closed')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    self_evaluation_score = models.IntegerField(null=True, blank=True)
    manager_evaluation_score = models.IntegerField(null=True, blank=True)
    overall_rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Feedback(models.Model):
    TYPE_CHOICES = [('positive','Positive'),('constructive','Constructive'),('general','General')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    given_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    feedback_text = models.TextField()
    feedback_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    created_date = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

