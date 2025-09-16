from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Real-time User Management API
    path('api/create-user/', views.create_user_api, name='create_user_api'),
]
