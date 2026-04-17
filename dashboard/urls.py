from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_panel, name='admin_panel'),
    path('api/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/activity/', views.recent_activity, name='recent_activity'),
    path('api/calendar/', views.appointment_calendar, name='appointment_calendar'),
]
