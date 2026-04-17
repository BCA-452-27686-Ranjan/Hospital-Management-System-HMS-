from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from .forms import (
    CustomUserCreationForm, PatientRegistrationForm, DoctorRegistrationForm,
    UserUpdateForm, PatientProfileUpdateForm, DoctorProfileUpdateForm
)
from .models import User, PatientProfile, DoctorProfile

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return reverse_lazy('dashboard:admin_panel')
        elif user.role == 'DOCTOR':
            return reverse_lazy('appointments:doctor_dashboard')
        else:
            return reverse_lazy('dashboard:home')

class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            
            # Auto-login after registration
            user = authenticate(username=user.username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('accounts:profile_setup')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_setup(request):
    user = request.user
    
    if user.role == 'PATIENT':
        profile, created = PatientProfile.objects.get_or_create(user=user)
        form_class = PatientRegistrationForm
        template = 'accounts/patient_profile_setup.html'
    elif user.role == 'DOCTOR':
        profile, created = DoctorProfile.objects.get_or_create(user=user)
        form_class = DoctorRegistrationForm
        template = 'accounts/doctor_profile_setup.html'
    else:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        # Handle profile picture upload
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            # Validate file
            if not profile_picture.content_type.startswith('image/'):
                messages.error(request, 'Please upload a valid image file.')
                return redirect('accounts:profile_setup')
            
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                messages.error(request, 'Profile picture must be smaller than 5MB.')
                return redirect('accounts:profile_setup')
            
            profile.profile_picture = profile_picture
        
        # Update user fields
        user.date_of_birth = request.POST.get('date_of_birth') or user.date_of_birth
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        # Handle profile form
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile setup completed successfully!')
            return redirect('dashboard:home')
    else:
        form = form_class(instance=profile)
    
    return render(request, template, {'form': form, 'user': user})

@login_required
def profile_view(request):
    user = request.user
    
    if user.role == 'PATIENT':
        try:
            profile = user.patient_profile
        except PatientProfile.DoesNotExist:
            profile = None
    elif user.role == 'DOCTOR':
        try:
            profile = user.doctor_profile
        except DoctorProfile.DoesNotExist:
            profile = None
    else:
        profile = None
    
    # Get profile image URL
    profile_image = user.get_profile_picture_url()
    
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'profile_image': profile_image,
    })

@login_required
def edit_profile(request):
    user = request.user
    
    if user.role == 'PATIENT':
        try:
            profile = user.patient_profile
        except PatientProfile.DoesNotExist:
            profile = PatientProfile.objects.create(user=user)
        
        if request.method == 'POST':
            # Handle profile picture removal
            if request.POST.get('remove_profile_picture'):
                if profile.profile_picture:
                    profile.profile_picture.delete()
                    profile.profile_picture = None
                messages.success(request, 'Profile picture removed successfully!')
                return redirect('accounts:profile')
            
            # Handle profile picture upload
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                # Validate file
                if not profile_picture.content_type.startswith('image/'):
                    messages.error(request, 'Please upload a valid image file.')
                    return redirect('accounts:edit_profile')
                
                if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, 'Profile picture must be smaller than 5MB.')
                    return redirect('accounts:edit_profile')
                
                profile.profile_picture = profile_picture
            
            # Update user fields
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone = request.POST.get('phone', user.phone)
            user.date_of_birth = request.POST.get('date_of_birth') or user.date_of_birth
            user.save()
            
            # Update profile fields
            profile.emergency_contact_name = request.POST.get('emergency_contact_name', profile.emergency_contact_name)
            profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', profile.emergency_contact_phone)
            profile.gender = request.POST.get('gender', profile.gender)
            profile.blood_group = request.POST.get('blood_group', profile.blood_group)
            profile.medical_history = request.POST.get('medical_history', profile.medical_history)
            profile.allergies = request.POST.get('allergies', profile.allergies)
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        
        return render(request, 'accounts/edit_profile.html', {'user': user})
    
    elif user.role == 'DOCTOR':
        try:
            profile = user.doctor_profile
        except DoctorProfile.DoesNotExist:
            profile = DoctorProfile.objects.create(
                user=user,
                specialization='GEN',  # Default to General Physician
                license_number='TEMP-' + str(user.id),  # Temporary license number
                qualification='Not specified',
                available_days='Mon,Tue,Wed,Thu,Fri',  # Default weekdays
            )
        
        if request.method == 'POST':
            # Handle profile picture removal
            if request.POST.get('remove_profile_picture'):
                if profile.profile_picture:
                    profile.profile_picture.delete()
                    profile.profile_picture = None
                messages.success(request, 'Profile picture removed successfully!')
                return redirect('accounts:profile')
            
            # Handle profile picture upload
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                # Validate file
                if not profile_picture.content_type.startswith('image/'):
                    messages.error(request, 'Please upload a valid image file.')
                    return redirect('accounts:edit_profile')
                
                if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, 'Profile picture must be smaller than 5MB.')
                    return redirect('accounts:edit_profile')
                
                profile.profile_picture = profile_picture
            
            # Update user fields
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone = request.POST.get('phone', user.phone)
            user.save()
            
            # Update profile fields
            profile.specialization = request.POST.get('specialization', profile.specialization)
            profile.experience_years = request.POST.get('experience_years', profile.experience_years)
            profile.consultation_fee = request.POST.get('consultation_fee', profile.consultation_fee)
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        
        return render(request, 'accounts/edit_profile.html', {'user': user})
    
    else:
        # Admin profile update
        if request.method == 'POST':
            # Handle profile picture removal
            if request.POST.get('remove_profile_picture'):
                if user.profile_picture:
                    user.profile_picture.delete()
                    user.profile_picture = None
                messages.success(request, 'Profile picture removed successfully!')
                return redirect('accounts:profile')
            
            # Handle profile picture upload
            profile_picture = request.FILES.get('profile_picture')
            if profile_picture:
                # Validate file
                if not profile_picture.content_type.startswith('image/'):
                    messages.error(request, 'Please upload a valid image file.')
                    return redirect('accounts:edit_profile')
                
                if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, 'Profile picture must be smaller than 5MB.')
                    return redirect('accounts:edit_profile')
                
                user.profile_picture = profile_picture
            
            # Update user fields
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        
        return render(request, 'accounts/edit_profile.html', {'user': user})
