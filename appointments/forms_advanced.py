from django import forms
from django.contrib.auth import get_user_model
from .models import Appointment, MedicalRecord, PatientFeedback
from accounts.models import User

User = get_user_model()

class AdvancedSearchForm(forms.Form):
    """Advanced search form for appointments"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by patient name, email, phone, or notes...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Appointment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priority')] + Appointment.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='DOCTOR'),
        required=False,
        empty_label="All Doctors",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(role='PATIENT'),
        required=False,
        empty_label="All Patients",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel')
        ],
        initial='csv',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class MedicalRecordSearchForm(forms.Form):
    """Search form for medical records"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by diagnosis, symptoms, treatment, or prescription...'
        })
    )
    
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='DOCTOR'),
        required=False,
        empty_label="All Doctors",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(role='PATIENT'),
        required=False,
        empty_label="All Patients",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel')
        ],
        initial='csv',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserManagementForm(forms.Form):
    """User management form for admins"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, email, or name...'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + User.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class BulkActionForm(forms.Form):
    """Form for bulk actions on appointments"""
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('confirm', 'Confirm Selected'),
            ('cancel', 'Cancel Selected'),
            ('complete', 'Mark as Completed'),
            ('delete', 'Delete Selected'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    selected_appointments = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

class AppointmentAnalyticsForm(forms.Form):
    """Form for appointment analytics"""
    date_range = forms.ChoiceField(
        choices=[
            ('7', 'Last 7 Days'),
            ('30', 'Last 30 Days'),
            ('90', 'Last 90 Days'),
            ('365', 'Last Year'),
            ('custom', 'Custom Range'),
        ],
        initial='30',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('day', 'By Day'),
            ('week', 'By Week'),
            ('month', 'By Month'),
            ('doctor', 'By Doctor'),
            ('status', 'By Status'),
            ('priority', 'By Priority'),
        ],
        initial='day',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class PermissionForm(forms.Form):
    """Form for managing user permissions"""
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    permissions = forms.MultipleChoiceField(
        choices=[
            ('view_own_appointments', 'View Own Appointments'),
            ('view_all_appointments', 'View All Appointments'),
            ('manage_appointments', 'Manage Appointments'),
            ('manage_users', 'Manage Users'),
            ('view_medical_records', 'View Medical Records'),
            ('create_medical_records', 'Create Medical Records'),
            ('export_data', 'Export Data'),
            ('view_analytics', 'View Analytics'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
