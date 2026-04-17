from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, PatientProfile, DoctorProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(required=False, help_text="Enter phone number with country code")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['gender', 'blood_group', 'medical_history', 'allergies', 
                 'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }

class DoctorRegistrationForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'license_number', 'experience_years', 
                 'qualification', 'consultation_fee', 'available_days',
                 'available_time_start', 'available_time_end']
        widgets = {
            'available_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'available_time_end': forms.TimeInput(attrs={'type': 'time'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'address', 'profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class PatientProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['gender', 'blood_group', 'medical_history', 'allergies', 
                 'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }

class DoctorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'experience_years', 'qualification', 
                 'consultation_fee', 'available_days', 'available_time_start', 'available_time_end']
        widgets = {
            'available_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'available_time_end': forms.TimeInput(attrs={'type': 'time'}),
        }
