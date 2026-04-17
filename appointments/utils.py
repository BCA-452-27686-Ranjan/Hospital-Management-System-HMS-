from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View
from django.shortcuts import redirect
from django.contrib import messages
import csv
import xlsxwriter
import io
from datetime import datetime
from .models import Appointment, MedicalRecord, PatientFeedback
from accounts.models import User
import django.db.models as models

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.role == 'ADMIN'

class DoctorRequiredMixin(UserPassesTestMixin):
    """Mixin to require doctor role"""
    def test_func(self):
        return self.request.user.role == 'DOCTOR'

class PatientRequiredMixin(UserPassesTestMixin):
    """Mixin to require patient role"""
    def test_func(self):
        return self.request.user.role == 'PATIENT'

class OwnerOrAdminMixin(UserPassesTestMixin):
    """Mixin to require object owner or admin"""
    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        if user.role == 'ADMIN':
            return True
        elif hasattr(obj, 'patient'):
            return obj.patient == user
        elif hasattr(obj, 'doctor'):
            return obj.doctor == user
        return False

def export_appointments_to_csv(appointments, filename='appointments'):
    """Export appointments to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Patient Name', 'Patient Email', 'Doctor', 'Date', 'Time', 
        'Status', 'Priority', 'Created At', 'Notes'
    ])
    
    for apt in appointments:
        writer.writerow([
            apt.pk,
            apt.patient_name,
            apt.patient_email,
            f"Dr. {apt.doctor.get_full_name()}",
            apt.appointment_date.strftime('%Y-%m-%d'),
            apt.appointment_date.strftime('%H:%M'),
            apt.get_status_display(),
            apt.get_priority_display(),
            apt.created_at.strftime('%Y-%m-%d %H:%M'),
            apt.patient_notes[:100] + '...' if len(apt.patient_notes) > 100 else apt.patient_notes
        ])
    
    return response

def export_appointments_to_excel(appointments, filename='appointments'):
    """Export appointments to Excel format"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Appointments')
    
    # Add headers
    headers = [
        'ID', 'Patient Name', 'Patient Email', 'Patient Phone', 'Doctor', 
        'Date', 'Time', 'Status', 'Priority', 'Created At', 'Notes'
    ]
    for col_num, header in enumerate(headers, 1):
        worksheet.write(1, col_num, header)
    
    # Add data
    for row_num, apt in enumerate(appointments, 2):
        worksheet.write(row_num, 1, apt.pk)
        worksheet.write(row_num, 2, apt.patient_name)
        worksheet.write(row_num, 3, apt.patient_email)
        worksheet.write(row_num, 4, apt.patient_mobile)
        worksheet.write(row_num, 5, f"Dr. {apt.doctor.get_full_name()}")
        worksheet.write(row_num, 6, apt.appointment_date.strftime('%Y-%m-%d'))
        worksheet.write(row_num, 7, apt.appointment_date.strftime('%H:%M'))
        worksheet.write(row_num, 8, apt.get_status_display())
        worksheet.write(row_num, 9, apt.get_priority_display())
        worksheet.write(row_num, 10, apt.created_at.strftime('%Y-%m-%d %H:%M'))
        worksheet.write(row_num, 11, apt.patient_notes[:200] if apt.patient_notes else '')
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    
    return response

def export_medical_records_to_csv(medical_records, filename='medical_records'):
    """Export medical records to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Patient Name', 'Doctor', 'Diagnosis', 'Symptoms', 
        'Treatment', 'Prescription', 'Next Visit', 'Created At'
    ])
    
    for record in medical_records:
        writer.writerow([
            record.pk,
            record.patient.get_full_name(),
            f"Dr. {record.doctor.get_full_name()}",
            record.diagnosis,
            record.symptoms,
            record.treatment,
            record.prescription,
            record.next_visit_date.strftime('%Y-%m-%d') if record.next_visit_date else '',
            record.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

def advanced_appointment_search(queryset, search_query=None, status=None, priority=None, 
                               date_from=None, date_to=None, doctor=None, patient=None):
    """Advanced search functionality for appointments"""
    if search_query:
        queryset = queryset.filter(
            models.Q(patient_name__icontains=search_query) |
            models.Q(patient_email__icontains=search_query) |
            models.Q(patient_mobile__icontains=search_query) |
            models.Q(doctor_notes__icontains=search_query) |
            models.Q(patient_notes__icontains=search_query)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    if priority:
        queryset = queryset.filter(priority=priority)
    
    if date_from:
        queryset = queryset.filter(appointment_date__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(appointment_date__date__lte=date_to)
    
    if doctor:
        queryset = queryset.filter(doctor=doctor)
    
    if patient:
        queryset = queryset.filter(patient=patient)
    
    return queryset.order_by('-appointment_date')

def paginate_queryset(queryset, page_number=1, items_per_page=10):
    """Helper function for pagination"""
    paginator = Paginator(queryset, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(1)
    
    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
    }

def get_appointment_statistics(queryset):
    """Calculate statistics for appointment queryset"""
    total = queryset.count()
    completed = queryset.filter(status='COMPLETED').count()
    cancelled = queryset.filter(status='CANCELLED').count()
    pending = queryset.filter(status='PENDING').count()
    scheduled = queryset.filter(status='SCHEDULED').count()
    
    return {
        'total': total,
        'completed': completed,
        'cancelled': cancelled,
        'pending': pending,
        'scheduled': scheduled,
        'completion_rate': round((completed / total * 100), 2) if total > 0 else 0,
        'cancellation_rate': round((cancelled / total * 100), 2) if total > 0 else 0,
    }

def check_permission(user, required_permission, obj=None):
    """Check if user has required permission"""
    if user.role == 'ADMIN':
        return True
    
    permission_map = {
        'view_own_appointments': ['PATIENT', 'DOCTOR'],
        'view_all_appointments': ['ADMIN'],
        'manage_appointments': ['DOCTOR', 'ADMIN'],
        'manage_users': ['ADMIN'],
        'view_medical_records': ['DOCTOR', 'ADMIN'],
        'create_medical_records': ['DOCTOR', 'ADMIN'],
        'export_data': ['ADMIN'],
    }
    
    allowed_roles = permission_map.get(required_permission, [])
    
    if user.role not in allowed_roles:
        return False
    
    # Check object-level permissions
    if obj and required_permission in ['view_own_appointments', 'manage_appointments']:
        if hasattr(obj, 'patient') and user.role == 'PATIENT':
            return obj.patient == user
        elif hasattr(obj, 'doctor') and user.role == 'DOCTOR':
            return obj.doctor == user
    
    return True
