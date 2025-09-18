from django.urls import path
from . import views
app_name = 'performance'

urlpatterns = [
    path('goals/', views.goals, name='goals'),
    path('goals/update/<int:pk>/', views.update_goal_status, name='update_goal_status'),
    path('reviews/', views.reviews, name='reviews'),
    path('feedback/', views.feedback, name='feedback'),
]

