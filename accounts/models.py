from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PATIENT')
    phone = PhoneNumberField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/img/default-avatar.png'

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    medical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = PhoneNumberField(blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"Patient: {self.user.full_name}"
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/img/default-patient-avatar.png'

class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('CARD', 'Cardiologist'),
        ('NEUR', 'Neurologist'),
        ('ORTH', 'Orthopedic'),
        ('PED', 'Pediatrician'),
        ('DERM', 'Dermatologist'),
        ('GEN', 'General Physician'),
        ('GYN', 'Gynecologist'),
        ('OPH', 'Ophthalmologist'),
        ('ENT', 'ENT Specialist'),
        ('PSY', 'Psychiatrist'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    qualification = models.CharField(max_length=200)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    available_days = models.CharField(max_length=100, help_text="Comma separated days: Mon,Tue,Wed,Thu,Fri,Sat,Sun")
    available_time_start = models.TimeField(default='09:00')
    available_time_end = models.TimeField(default='17:00')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"Dr. {self.user.full_name} ({self.get_specialization_display()})"
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/img/default-doctor-avatar.png'
    
    def get_available_days_list(self):
        if self.available_days:
            return [day.strip().capitalize() for day in self.available_days.split(',')]
        return []

class MedicalReport(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_reports')
    title = models.CharField(max_length=200)
    report_file = models.FileField(upload_to='medical_reports/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    report_date = models.DateField(help_text="Date of medical report")
    description = models.TextField(blank=True, help_text="Brief description of report")
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Medical Report'
        verbose_name_plural = 'Medical Reports'
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.title}"
    
    def get_filename(self):
        return self.report_file.name.split('/')[-1]
