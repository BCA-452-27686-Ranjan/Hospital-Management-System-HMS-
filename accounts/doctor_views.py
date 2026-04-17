from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Avg
from .models import User, DoctorProfile
from appointments.models import Schedule, Appointment, PatientFeedback

@login_required
def doctor_list(request):
    """View for patients to see all available doctors"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'This feature is only available for patients.')
        return redirect('dashboard:home')
    
    # Get all doctors with their profiles
    doctors = User.objects.filter(role='DOCTOR').select_related('doctor_profile')
    
    # Filter by specialization if provided
    specialization_filter = request.GET.get('specialization')
    if specialization_filter:
        doctors = doctors.filter(doctor_profile__specialization=specialization_filter)
    
    # Calculate statistics for each doctor and handle profile pictures
    doctors_with_stats = []
    for doctor in doctors:
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        completed_appointments = Appointment.objects.filter(doctor=doctor, status='COMPLETED').count()
        
        # Add stats as attributes to doctor object
        doctor.total_appointments = total_appointments
        doctor.completed_appointments = completed_appointments
        
        # Handle profile picture URL
        profile_image_url = doctor.get_profile_picture_url()
        doctor.profile_image_url = profile_image_url
        
        doctors_with_stats.append(doctor)
    
    # Pagination
    paginator = Paginator(doctors_with_stats, 12)  # 12 doctors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all specializations for filter dropdown
    specializations = DoctorProfile.objects.values_list('specialization', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'specializations': specializations,
        'current_specialization': specialization_filter,
    }
    
    return render(request, 'accounts/doctor_list.html', context)

@login_required
def doctor_profile_view(request, doctor_id):
    """View for patients to see a specific doctor's profile (read-only)"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'This feature is only available for patients.')
        return redirect('dashboard:home')
    
    doctor = get_object_or_404(User, id=doctor_id, role='DOCTOR')
    
    try:
        doctor_profile = doctor.doctor_profile
    except DoctorProfile.DoesNotExist:
        doctor_profile = None
    
    # Get doctor's weekly schedule (not specific dates)
    schedules = Schedule.objects.filter(
        doctor=doctor,
        is_active=True
    ).order_by('day_of_week', 'start_time')
    
    # Get doctor's statistics
    completed_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='COMPLETED'
    ).count()
    
    # Get patient feedback for this doctor
    feedback_list = PatientFeedback.objects.filter(doctor=doctor).order_by('-created_at')
    feedback_count = feedback_list.count()
    avg_rating = feedback_list.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Handle profile picture URL
    profile_image_url = doctor.get_profile_picture_url()
    
    context = {
        'doctor': doctor,
        'doctor_profile': doctor_profile,
        'schedules': schedules,
        'completed_appointments': completed_appointments,
        'profile_image': profile_image_url,
        'feedback_list': feedback_list,
        'feedback_count': feedback_count,
        'average_rating': round(avg_rating, 1),
    }
    
    return render(request, 'accounts/doctor_profile_view.html', context)
