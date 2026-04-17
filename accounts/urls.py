from django.urls import path
from . import views
from . import views_simple
from . import doctor_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # Doctor listing and profile viewing for patients
    path('doctors/', doctor_views.doctor_list, name='doctor_list'),
    path('doctor/<int:doctor_id>/', doctor_views.doctor_profile_view, name='doctor_profile'),
    
    # Simple registration
    path('simple-register/', views_simple.simple_register, name='simple_register'),
]
