from django.urls import path
from . import views

urlpatterns = [
    # Welcome and health endpoints
    path('', views.api_welcome, name='api-welcome'),
    path('health/', views.health_check, name='health-check'),
    
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    
    # Reference data endpoints
    path('materials/', views.MaterialListView.as_view(), name='materials-list'),
    path('machines/', views.MachineListView.as_view(), name='machines-list'),
    
    # Deposit endpoints
    path('deposits/', views.create_deposit, name='create-deposit'),
    path('deposits/history/', views.user_deposits, name='user-deposits'),
    
    # User summary endpoint
    path('user/summary/', views.user_summary, name='user-summary'),
    
    # System statistics (admin only)
    path('admin/stats/', views.system_stats, name='system-stats'),
]
