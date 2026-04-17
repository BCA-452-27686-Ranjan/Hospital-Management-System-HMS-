from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q
from accounts.models import User, PatientProfile, DoctorProfile
from appointments.models import Appointment
import json
from datetime import timedelta

@login_required
def home(request):
    context = {}
    
    # Add user profile information
    try:
        if request.user.role == 'DOCTOR':
            try:
                doctor_profile = request.user.doctor_profile
                profile_image = request.user.get_profile_picture_url()
                context.update({
                    'user_profile': doctor_profile,
                    'profile_image': profile_image,
                    'specialization': doctor_profile.get_specialization_display() if doctor_profile.specialization else None,
                    'experience': doctor_profile.experience_years,
                })
            except:
                # Fallback if doctor profile doesn't exist
                profile_image = request.user.get_profile_picture_url()
                context.update({
                    'user_profile': None,
                    'profile_image': profile_image,
                    'specialization': None,
                    'experience': None,
                })
        elif request.user.role == 'PATIENT':
            try:
                patient_profile = request.user.patient_profile
                profile_image = request.user.get_profile_picture_url()
                context.update({
                    'user_profile': patient_profile,
                    'profile_image': profile_image,
                    'date_of_birth': patient_profile.date_of_birth,
                    'blood_group': patient_profile.blood_group,
                })
            except:
                # Fallback if patient profile doesn't exist
                profile_image = request.user.get_profile_picture_url()
                context.update({
                    'user_profile': None,
                    'profile_image': profile_image,
                    'date_of_birth': None,
                    'blood_group': None,
                })
        else:
            # Admin user
            profile_image = request.user.get_profile_picture_url()
            context.update({
                'user_profile': None,
                'profile_image': profile_image,
            })
    except Exception as e:
        # Ultimate fallback
        context.update({
            'user_profile': None,
            'profile_image': '/static/img/default-avatar.png',
        })
        print(f"Error getting profile picture: {e}")
    
    if request.user.role == 'ADMIN':
        # Admin stats
        context.update({
            'total_patients': User.objects.filter(role='PATIENT').count(),
            'total_doctors': User.objects.filter(role='DOCTOR').count(),
            'total_appointments': Appointment.objects.count(),
            'today_appointments': Appointment.objects.filter(
                appointment_date__date=timezone.now().date()
            ).count(),
        })
        
        # Add admin profile information
        try:
            profile_image = request.user.get_profile_picture_url()
            context.update({
                'user_profile': None,
                'profile_image': profile_image,
            })
        except:
            context.update({
                'user_profile': None,
                'profile_image': '/static/img/default-avatar.png',
            })
    elif request.user.role == 'DOCTOR':
        # Doctor stats
        doctor = request.user
        today = timezone.now().date()
        context.update({
            'today_appointments': Appointment.objects.filter(
                doctor=doctor,
                appointment_date__date=today
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='PENDING'
            ).count(),
            'scheduled_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='SCHEDULED'
            ).count(),
            'completed_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='COMPLETED'
            ).count(),
        })
    elif request.user.role == 'PATIENT':
        # Patient stats
        patient = request.user
        context.update({
            'total_appointments': Appointment.objects.filter(patient=patient).count(),
            'upcoming_appointments': Appointment.objects.filter(
                patient=patient,
                appointment_date__gt=timezone.now(),
                status='SCHEDULED'
            ).count(),
            'completed_appointments': Appointment.objects.filter(
                patient=patient,
                status='COMPLETED'
            ).count(),
        })
    
    return render(request, 'dashboard/home.html', context)

@login_required
def admin_panel(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard:home')
    
    context = {
        'total_patients': User.objects.filter(role='PATIENT').count(),
        'total_doctors': User.objects.filter(role='DOCTOR').count(),
        'total_appointments': Appointment.objects.count(),
        'today_appointments': Appointment.objects.filter(
            appointment_date__date=timezone.now().date()
        ).count(),
        'recent_patients': User.objects.filter(role='PATIENT').order_by('-date_joined')[:5],
        'recent_doctors': User.objects.filter(role='DOCTOR').order_by('-date_joined')[:5],
        'recent_appointments': Appointment.objects.order_by('-created_at')[:5],
    }
    
    return render(request, 'dashboard/admin_panel.html', context)

@login_required
def dashboard_stats(request):
    """API endpoint for real-time dashboard statistics"""
    if request.user.role == 'ADMIN':
        stats = {
            'total_patients': User.objects.filter(role='PATIENT').count(),
            'total_doctors': User.objects.filter(role='DOCTOR').count(),
            'total_appointments': Appointment.objects.count(),
            'today_appointments': Appointment.objects.filter(
                appointment_date__date=timezone.now().date()
            ).count(),
        }
    elif request.user.role == 'DOCTOR':
        doctor = request.user
        today = timezone.now().date()
        stats = {
            'today_appointments': Appointment.objects.filter(
                doctor=doctor,
                appointment_date__date=today
            ).count(),
            'pending_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='PENDING'
            ).count(),
            'scheduled_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='SCHEDULED'
            ).count(),
            'completed_appointments': Appointment.objects.filter(
                doctor=doctor,
                status='COMPLETED'
            ).count(),
        }
    elif request.user.role == 'PATIENT':
        patient = request.user
        stats = {
            'total_appointments': Appointment.objects.filter(patient=patient).count(),
            'upcoming_appointments': Appointment.objects.filter(
                patient=patient,
                appointment_date__gt=timezone.now(),
                status='SCHEDULED'
            ).count(),
            'completed_appointments': Appointment.objects.filter(
                patient=patient,
                status='COMPLETED'
            ).count(),
        }
    else:
        stats = {}
    
    return JsonResponse(stats)

@login_required
def recent_activity(request):
    """API endpoint for recent activity feed"""
    if request.user.role == 'ADMIN':
        # Admin sees all recent activity
        recent_appointments = Appointment.objects.order_by('-created_at')[:10]
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        activity = []
        for apt in recent_appointments:
            activity.append({
                'type': 'appointment',
                'message': f'{apt.patient_name} booked appointment with Dr. {apt.doctor.get_full_name()}',
                'time': apt.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': apt.get_status_display()
            })
        
        for user in recent_users:
            activity.append({
                'type': 'user',
                'message': f'New {user.get_role_display()}: {user.get_full_name() or user.username}',
                'time': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                'status': 'Active'
            })
            
    elif request.user.role == 'DOCTOR':
        # Doctor sees their recent appointments
        recent_appointments = Appointment.objects.filter(
            doctor=request.user
        ).order_by('-created_at')[:10]
        
        activity = []
        for apt in recent_appointments:
            activity.append({
                'type': 'appointment',
                'message': f'Appointment with {apt.patient_name}',
                'time': apt.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': apt.get_status_display()
            })
            
    elif request.user.role == 'PATIENT':
        # Patient sees their recent appointments
        recent_appointments = Appointment.objects.filter(
            patient=request.user
        ).order_by('-created_at')[:10]
        
        activity = []
        for apt in recent_appointments:
            activity.append({
                'type': 'appointment',
                'message': f'Appointment with Dr. {apt.doctor.get_full_name()}',
                'time': apt.created_at.strftime('%Y-%m-%d %H:%M'),
                'status': apt.get_status_display()
            })
    else:
        activity = []
    
    return JsonResponse({'activity': activity})

@login_required
def appointment_calendar(request):
    """API endpoint for calendar view"""
    if request.user.role == 'DOCTOR':
        appointments = Appointment.objects.filter(doctor=request.user)
    elif request.user.role == 'PATIENT':
        appointments = Appointment.objects.filter(patient=request.user)
    else:
        appointments = Appointment.objects.all()
    
    # Convert to calendar format
    events = []
    for apt in appointments:
        events.append({
            'title': f"{apt.patient_name} - {apt.get_status_display()}",
            'start': apt.appointment_date.isoformat(),
            'color': {
                'PENDING': '#ffc107',
                'SCHEDULED': '#007bff',
                'COMPLETED': '#28a745',
                'CANCELLED': '#dc3545',
                'EXPIRED': '#6c757d'
            }.get(apt.status, '#007bff'),
            'url': f"/appointments/appointment/{apt.pk}/"
        })
    
    return JsonResponse({'events': events})
