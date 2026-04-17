from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'profile_picture', 'date_of_birth', 'address')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'email', 'first_name', 'last_name', 'phone')
        }),
    )

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'blood_group', 'emergency_contact_name')
    list_filter = ('gender', 'blood_group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'emergency_contact_name')
    raw_id_fields = ('user',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'experience_years', 'consultation_fee')
    list_filter = ('specialization', 'experience_years')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'license_number')
    raw_id_fields = ('user',)
