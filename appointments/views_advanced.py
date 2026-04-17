from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Appointment, MedicalRecord, PatientFeedback
from .utils import (
    AdminRequiredMixin, DoctorRequiredMixin, PatientRequiredMixin,
    export_appointments_to_csv, export_appointments_to_excel,
    advanced_appointment_search, paginate_queryset, get_appointment_statistics,
    check_permission
)
from accounts.models import User
import django

User = get_user_model()

@login_required
def advanced_search(request):
    """Advanced search page for appointments"""
    if not check_permission(request.user, 'view_all_appointments'):
        messages.error(request, 'You do not have permission to access advanced search.')
        return redirect('dashboard:home')
    
    queryset = Appointment.objects.all()
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    doctor_id = request.GET.get('doctor', '')
    patient_id = request.GET.get('patient', '')
    
    # Apply filters
    doctor = User.objects.filter(pk=doctor_id, role='DOCTOR').first() if doctor_id else None
    patient = User.objects.filter(pk=patient_id, role='PATIENT').first() if patient_id else None
    
    queryset = advanced_appointment_search(
        queryset, search_query, status, priority,
        date_from, date_to, doctor, patient
    )
    
    # Pagination
    page_number = request.GET.get('page', 1)
    pagination_data = paginate_queryset(queryset, page_number, items_per_page=20)
    
    # Get filter options
    doctors = User.objects.filter(role='DOCTOR')
    patients = User.objects.filter(role='PATIENT')
    
    context = {
        'page_obj': pagination_data['page_obj'],
        'paginator': pagination_data['paginator'],
        'has_next': pagination_data['has_next'],
        'has_previous': pagination_data['has_previous'],
        'next_page_number': pagination_data['next_page_number'],
        'previous_page_number': pagination_data['previous_page_number'],
        'search_query': search_query,
        'selected_status': status,
        'selected_priority': priority,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
        'selected_doctor': doctor_id,
        'selected_patient': patient_id,
        'doctors': doctors,
        'patients': patients,
        'statistics': get_appointment_statistics(queryset),
    }
    
    return render(request, 'appointments/advanced_search.html', context)

@login_required
def export_appointments(request):
    """Export appointments based on search criteria"""
    if not check_permission(request.user, 'export_data'):
        messages.error(request, 'You do not have permission to export data.')
        return redirect('dashboard:home')
    
    export_format = request.GET.get('format', 'csv')
    
    # Get filtered appointments
    queryset = Appointment.objects.all()
    search_query = request.GET.get('search', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    doctor_id = request.GET.get('doctor', '')
    patient_id = request.GET.get('patient', '')
    
    doctor = User.objects.filter(pk=doctor_id, role='DOCTOR').first() if doctor_id else None
    patient = User.objects.filter(pk=patient_id, role='PATIENT').first() if patient_id else None
    
    appointments = advanced_appointment_search(
        queryset, search_query, status, priority,
        date_from, date_to, doctor, patient
    )
    
    if export_format == 'excel':
        return export_appointments_to_excel(appointments)
    else:
        return export_appointments_to_csv(appointments)

@login_required
def export_medical_records(request):
    """Export medical records"""
    if not check_permission(request.user, 'view_medical_records'):
        messages.error(request, 'You do not have permission to export medical records.')
        return redirect('dashboard:home')
    
    export_format = request.GET.get('format', 'csv')
    
    # Get filtered medical records
    queryset = MedicalRecord.objects.all()
    search_query = request.GET.get('search', '')
    doctor_id = request.GET.get('doctor', '')
    patient_id = request.GET.get('patient', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        queryset = queryset.filter(
            Q(diagnosis__icontains=search_query) |
            Q(symptoms__icontains=search_query) |
            Q(treatment__icontains=search_query) |
            Q(prescription__icontains=search_query)
        )
    
    if doctor_id:
        doctor = User.objects.filter(pk=doctor_id, role='DOCTOR').first()
        queryset = queryset.filter(doctor=doctor)
    
    if patient_id:
        patient = User.objects.filter(pk=patient_id, role='PATIENT').first()
        queryset = queryset.filter(patient=patient)
    
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    
    if export_format == 'excel':
        return export_medical_records_to_excel(queryset)
    else:
        return export_medical_records_to_csv(queryset)

class AppointmentAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Analytics view for appointment data"""
    model = Appointment
    template_name = 'appointments/analytics.html'
    context_object_name = 'appointments'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Appointment.objects.all()
        
        # Apply filters from GET parameters
        search_query = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        doctor_id = self.request.GET.get('doctor', '')
        patient_id = self.request.GET.get('patient', '')
        
        doctor = User.objects.filter(pk=doctor_id, role='DOCTOR').first() if doctor_id else None
        patient = User.objects.filter(pk=patient_id, role='PATIENT').first() if patient_id else None
        
        return advanced_appointment_search(
            queryset, search_query, status, priority,
            date_from, date_to, doctor, patient
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        context['statistics'] = get_appointment_statistics(self.get_queryset())
        
        # Add filter options
        context['doctors'] = User.objects.filter(role='DOCTOR')
        context['patients'] = User.objects.filter(role='PATIENT')
        
        # Add current filters
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_priority'] = self.request.GET.get('priority', '')
        context['selected_date_from'] = self.request.GET.get('date_from', '')
        context['selected_date_to'] = self.request.GET.get('date_to', '')
        context['selected_doctor'] = self.request.GET.get('doctor', '')
        context['selected_patient'] = self.request.GET.get('patient', '')
        
        return context

@login_required
def permission_denied(request):
    """Custom permission denied view"""
    return render(request, 'appointments/permission_denied.html', {
        'message': 'You do not have permission to access this page.',
        'user_role': request.user.get_role_display()
    })

@login_required
def user_management(request):
    """Advanced user management for admins"""
    if not check_permission(request.user, 'manage_users'):
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('dashboard:home')
    
    users = User.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    pagination_data = paginate_queryset(users, page_number, items_per_page=20)
    
    context = {
        'page_obj': pagination_data['page_obj'],
        'paginator': pagination_data['paginator'],
        'has_next': pagination_data['has_next'],
        'has_previous': pagination_data['has_previous'],
        'next_page_number': pagination_data['next_page_number'],
        'previous_page_number': pagination_data['previous_page_number'],
        'search_query': search_query,
        'selected_role': role_filter,
        'total_users': users.count(),
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'appointments/user_management.html', context)

@login_required
def system_logs(request):
    """View system activity logs"""
    if not check_permission(request.user, 'view_all_appointments'):
        messages.error(request, 'You do not have permission to view system logs.')
        return redirect('dashboard:home')
    
    # Get recent activities
    recent_appointments = Appointment.objects.order_by('-created_at')[:100]
    recent_users = User.objects.order_by('-date_joined')[:50]
    
    context = {
        'recent_appointments': recent_appointments,
        'recent_users': recent_users,
        'total_appointments': Appointment.objects.count(),
        'total_users': User.objects.count(),
    }
    
    return render(request, 'appointments/system_logs.html', context)
