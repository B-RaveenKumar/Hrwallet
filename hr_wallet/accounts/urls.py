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

    # Admin User Management APIs
    path('api/users/', views.list_users_api, name='list_users_api'),
    path('api/users/export/', views.export_users_api, name='export_users_api'),
    path('api/users/bulk/', views.bulk_update_users_api, name='bulk_update_users_api'),
    path('api/users/<int:pk>/', views.user_detail_api, name='user_detail_api'),
    path('api/users/<int:pk>/update/', views.update_user_api, name='update_user_api'),
    path('api/users/<int:pk>/status/', views.change_user_status_api, name='change_user_status_api'),
]
