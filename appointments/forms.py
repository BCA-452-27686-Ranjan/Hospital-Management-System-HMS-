from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Appointment, MedicalRecord, PatientFeedback

User = get_user_model()

class MockPaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('NET_BANKING', 'Net Banking'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Payment Method"
    )
    
    # Card details
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'id': 'card-number'
        }),
        label="Card Number"
    )
    
    card_expiry = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'id': 'card-expiry'
        }),
        label="Expiry Date"
    )
    
    card_cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'id': 'card-cvv'
        }),
        label="CVV"
    )
    
    # UPI details
    upi_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'your-upi@upi or mobile@ybl',
            'id': 'upi-id'
        }),
        label="UPI ID"
    )
    
    # Net banking details
    bank_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State Bank of India',
            'id': 'bank-name'
        }),
        label="Bank Name"
    )
    
    account_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567890',
            'id': 'account-number'
        }),
        label="Account Number"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields required based on payment method
        self.fields['card_number'].widget.attrs['data-required-for'] = 'CARD'
        self.fields['card_expiry'].widget.attrs['data-required-for'] = 'CARD'
        self.fields['card_cvv'].widget.attrs['data-required-for'] = 'CARD'
        self.fields['upi_id'].widget.attrs['data-required-for'] = 'UPI'
        self.fields['bank_name'].widget.attrs['data-required-for'] = 'NET_BANKING'
        self.fields['account_number'].widget.attrs['data-required-for'] = 'NET_BANKING'
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        if payment_method == 'CARD':
            if not cleaned_data.get('card_number'):
                self.add_error('card_number', 'Card number is required for card payments.')
            if not cleaned_data.get('card_expiry'):
                self.add_error('card_expiry', 'Expiry date is required for card payments.')
            if not cleaned_data.get('card_cvv'):
                self.add_error('card_cvv', 'CVV is required for card payments.')
        
        elif payment_method == 'UPI':
            if not cleaned_data.get('upi_id'):
                self.add_error('upi_id', 'UPI ID is required for UPI payments.')
            else:
                upi_id = cleaned_data.get('upi_id')
                # Basic UPI ID validation (username@handle format)
                if '@' not in upi_id:
                    self.add_error('upi_id', 'UPI ID must be in format: username@upihandle')
                elif len(upi_id.split('@')[0]) < 3:
                    self.add_error('upi_id', 'UPI ID username must be at least 3 characters long.')
        
        elif payment_method == 'NET_BANKING':
            if not cleaned_data.get('bank_name'):
                self.add_error('bank_name', 'Bank name is required for net banking.')
            if not cleaned_data.get('account_number'):
                self.add_error('account_number', 'Account number is required for net banking.')
        
        return cleaned_data

class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'patient_name', 'patient_age', 'patient_address', 
                 'patient_phone', 'patient_email', 'reason', 'priority', 'notification_preference']
        widgets = {
            'patient_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'appointment_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'patient_phone': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'patient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'notification_preference': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        self.fields['doctor'].required = True
        self.fields['patient_name'].required = True
        self.fields['patient_age'].required = True
        self.fields['patient_phone'].required = True
        self.fields['priority'].required = True
        
        # Optional fields
        self.fields['reason'].required = False
        self.fields['patient_email'].required = False
        self.fields['patient_address'].required = False
        self.fields['notification_preference'].required = False
        
        # Filter doctors only and customize display
        doctors = User.objects.filter(role='DOCTOR')
        doctor_choices = []
        for doctor in doctors:
            full_name = doctor.get_full_name() or doctor.username
            # Add specialization if available
            if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile.specialization:
                specialization = doctor.doctor_profile.get_specialization_display()
                display_name = f"Dr. {full_name} - {specialization}"
            else:
                display_name = f"Dr. {full_name}"
            doctor_choices.append((doctor.id, display_name))
        
        self.fields['doctor'].choices = doctor_choices
        
        # Pre-fill patient information if user is logged in
        if user and user.role == 'PATIENT':
            self.fields['patient_name'].initial = user.get_full_name()
            self.fields['patient_email'].initial = user.email
            self.fields['patient_phone'].initial = user.phone
            if hasattr(user, 'patient_profile'):
                self.fields['patient_age'].initial = self._calculate_age(user.patient_profile)
                self.fields['patient_address'].initial = user.address
    
    def _calculate_age(self, patient_profile):
        if patient_profile.user.date_of_birth:
            today = timezone.now().date()
            born = patient_profile.user.date_of_birth
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None

class DoctorConfirmationForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'status', 'doctor_notes', 'follow_up_date']
        widgets = {
            'appointment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'doctor_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow certain status transitions
        if self.instance and self.instance.status == 'PENDING':
            self.fields['status'].choices = [
                ('SCHEDULED', 'Scheduled'),
                ('CANCELLED', 'Cancelled'),
            ]
        elif self.instance and self.instance.status == 'SCHEDULED':
            self.fields['status'].choices = [
                ('COMPLETED', 'Completed'),
                ('CANCELLED', 'Cancelled'),
            ]
        
        # Set minimum datetime to now
        self.fields['appointment_date'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'symptoms', 'treatment', 'prescription', 
                 'lab_results', 'notes', 'next_visit_date', 'is_chronic_condition']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter medical diagnosis...'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe patient symptoms...'}),
            'treatment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe treatment plan and medications...'}),
            'prescription': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter prescription details...'}),
            'lab_results': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter laboratory test results...'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Additional notes or observations...'}),
            'next_visit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_chronic_condition': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PatientFeedbackForm(forms.ModelForm):
    class Meta:
        model = PatientFeedback
        fields = ['rating', 'comments', 'would_recommend']
        widgets = {
            'rating': forms.RadioSelect(choices=PatientFeedback.RATING_CHOICES),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }

class AppointmentSearchForm(forms.Form):
    STATUS_CHOICES = [('', 'All Status')] + Appointment.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priority')] + Appointment.PRIORITY_CHOICES
    
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search by patient name or email...'
    }))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
