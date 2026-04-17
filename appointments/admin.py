from django.contrib import admin
from .models import Appointment, MedicalRecord, PatientFeedback

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'appointment_date', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'appointment_date', 'created_at')
    search_fields = ('patient_name', 'patient_email', 'doctor__first_name', 'doctor__last_name')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date',)
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient', 'patient_name', 'patient_age', 'patient_address', 
                      'patient_mobile', 'patient_email', 'patient_notes')
        }),
        ('Appointment Details', {
            'fields': ('doctor', 'appointment_date', 'status', 'priority')
        }),
        ('Doctor Information', {
            'fields': ('doctor_notes', 'prescribed_medication', 'follow_up_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'DOCTOR':
            return qs.filter(doctor=request.user)
        elif request.user.role == 'PATIENT':
            return qs.filter(patient=request.user)
        return qs

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment', 'created_at', 'is_chronic_condition')
    list_filter = ('is_chronic_condition', 'created_at', 'next_visit_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__first_name', 
                     'doctor__last_name', 'diagnosis')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'appointment')
        }),
        ('Medical Information', {
            'fields': ('diagnosis', 'symptoms', 'treatment', 'prescription', 
                      'lab_results', 'notes')
        }),
        ('Follow-up', {
            'fields': ('next_visit_date', 'is_chronic_condition')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'DOCTOR':
            return qs.filter(doctor=request.user)
        elif request.user.role == 'PATIENT':
            return qs.filter(patient=request.user)
        return qs

@admin.register(PatientFeedback)
class PatientFeedbackAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'patient', 'doctor', 'rating', 'would_recommend', 'created_at')
    list_filter = ('rating', 'would_recommend', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__first_name', 
                     'doctor__last_name', 'comments')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('appointment', 'patient', 'doctor')
        }),
        ('Feedback', {
            'fields': ('rating', 'comments', 'would_recommend')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'DOCTOR':
            return qs.filter(doctor=request.user)
        elif request.user.role == 'PATIENT':
            return qs.filter(patient=request.user)
        return qs
