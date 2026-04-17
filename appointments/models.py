from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import User

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('PENDING', 'Pending'),
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PAYMENT_SUCCESSFUL', 'Payment Successful'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    NOTIFICATION_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('BOTH', 'Both'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    notes = models.TextField(blank=True, null=True)
    patient_name = models.CharField(max_length=100, blank=True)
    patient_email = models.EmailField(blank=True)
    patient_phone = models.CharField(max_length=20, blank=True)
    patient_age = models.IntegerField(null=True, blank=True)
    patient_gender = models.CharField(max_length=10, blank=True)
    patient_address = models.TextField(blank=True)
    reason = models.TextField(blank=True, null=True)
    notification_preference = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES, default='EMAIL')
    
    # Doctor confirmation fields
    doctor_confirmed = models.BooleanField(default=False)
    doctor_notes = models.TextField(blank=True, null=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Notification fields
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    last_notification_at = models.DateTimeField(null=True, blank=True)
    
    # Follow-up fields
    follow_up_date = models.DateTimeField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True, null=True)
    follow_up_completed = models.BooleanField(default=False)
    
    # Payment fields
    payment_method = models.CharField(max_length=20, choices=[
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('NET_BANKING', 'Net Banking'),
    ], blank=True, null=True)
    
    payment_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
    ], default='PENDING', blank=True)
    
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    payment_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-created_at']
    
    def __str__(self):
        return f"{self.patient_name or self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} ({self.get_appointment_date_display()})"
    
    def get_appointment_date_display(self):
        if self.appointment_date:
            return self.appointment_date.strftime("%B %d, %Y at %I:%M %p")
        return "Date to be scheduled"
    
    def can_cancel(self):
        """Check if appointment can be cancelled"""
        if self.status in ['CANCELLED', 'COMPLETED', 'EXPIRED']:
            return False
        if self.appointment_date and self.appointment_date <= timezone.now() - timezone.timedelta(hours=2):
            return False
        return True
        # For SCHEDULED appointments, allow cancellation if it's today or in the future
        if self.status == 'SCHEDULED':
            return appointment_date >= today
        
        # For PENDING appointments, allow cancellation if it's today or in the future
        if self.status == 'PENDING':
            return appointment_date >= today
        
        return False
    
    @property
    def is_past(self):
        """Check if appointment is in the past"""
        if not self.appointment_date:
            return False
        return self.appointment_date <= timezone.now()
    
    @property
    def is_upcoming(self):
        return self.status == 'SCHEDULED' and self.appointment_date is not None and self.appointment_date > timezone.now()
    
    def save(self, *args, **kwargs):
        # Check if status is changing
        if self.pk:
            old_instance = Appointment.objects.get(pk=self.pk)
            status_changed = old_instance.status != self.status
            date_changed = old_instance.appointment_date != self.appointment_date
            
            # Send notifications based on status changes
            if status_changed:
                self.send_status_notification(old_instance.status, self.status)
            
            # Send reminder if date changed and appointment is scheduled
            if date_changed and self.status == 'SCHEDULED':
                self.reminder_sent = False  # Reset reminder flag
        
        # Auto-update status to EXPIRED if past due
        if self.is_past and self.status == 'SCHEDULED':
            self.status = 'EXPIRED'
        
        super().save(*args, **kwargs)
    
    def send_status_notification(self, old_status, new_status):
        """Send email notifications for status changes"""
        try:
            if new_status == 'SCHEDULED' and old_status == 'PENDING':
                # Appointment confirmed
                self.send_confirmation_email()
            elif new_status == 'CANCELLED':
                # Appointment cancelled
                self.send_cancellation_email()
            elif new_status == 'COMPLETED':
                # Appointment completed
                self.send_completion_email()
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def send_confirmation_email(self):
        """Send appointment confirmation email"""
        if self.notification_preference in ['EMAIL', 'BOTH'] and not self.email_sent:
            subject = 'Appointment Confirmed - Hospital Management System'
            message = render_to_string('appointments/email/confirmation.html', {
                'appointment': self,
                'patient': self.patient,
                'doctor': self.doctor,
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [self.patient_email],
                html_message=message,
                fail_silently=False,
            )
            self.email_sent = True
            Appointment.objects.filter(pk=self.pk).update(email_sent=True)
    
    def send_cancellation_email(self):
        """Send appointment cancellation email"""
        if self.notification_preference in ['EMAIL', 'BOTH']:
            subject = 'Appointment Cancelled - Hospital Management System'
            message = render_to_string('appointments/email/cancellation.html', {
                'appointment': self,
                'patient': self.patient,
                'doctor': self.doctor,
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [self.patient_email],
                html_message=message,
                fail_silently=False,
            )
    
    def send_completion_email(self):
        """Send appointment completion email with feedback request"""
        if self.notification_preference in ['EMAIL', 'BOTH']:
            subject = 'Appointment Completed - Thank You for Visiting'
            message = render_to_string('appointments/email/completion.html', {
                'appointment': self,
                'patient': self.patient,
                'doctor': self.doctor,
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [self.patient_email],
                html_message=message,
                fail_silently=False,
            )
    
    def send_reminder_email(self):
        """Send appointment reminder email"""
        if self.notification_preference in ['EMAIL', 'BOTH'] and not self.reminder_sent:
            subject = 'Appointment Reminder - Hospital Management System'
            message = render_to_string('appointments/email/reminder.html', {
                'appointment': self,
                'patient': self.patient,
                'doctor': self.doctor,
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [self.patient_email],
                html_message=message,
                fail_silently=False,
            )
            self.reminder_sent = True
            Appointment.objects.filter(pk=self.pk).update(reminder_sent=True)

class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_medical_records')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    
    # Medical information
    diagnosis = models.TextField()
    symptoms = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Follow-up
    next_visit_date = models.DateField(null=True, blank=True)
    is_chronic_condition = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
    
    def __str__(self):
        return f"Medical Record: {self.patient.get_full_name()} - {self.created_at.strftime('%Y-%m-%d')}"

class PatientFeedback(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='feedback')
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback')
    
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient Feedback'
        verbose_name_plural = 'Patient Feedback'
    
    def __str__(self):
        return f"Feedback: {self.patient.get_full_name()} for Dr. {self.doctor.get_full_name()} - {self.rating}/5"

class Schedule(models.Model):
    """Doctor's weekly schedule template"""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_patients_per_day = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week']
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


class PaymentSlip(models.Model):
    """Payment slip for appointments"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment_slip')
    slip_number = models.CharField(max_length=50, unique=True)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    patient_name = models.CharField(max_length=100)
    doctor_name = models.CharField(max_length=100)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='PAID')
    
    # File attachment
    slip_file = models.FileField(upload_to='payment_slips/%Y/%m/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment Slip {self.slip_number} - {self.patient_name}"
    
    def get_payment_method_display(self):
        """Get display text for payment method"""
        methods = {
            'CARD': 'Credit/Debit Card',
            'UPI': 'UPI',
            'NET_BANKING': 'Net Banking',
        }
        return methods.get(self.payment_method, self.payment_method)
    
    def generate_slip_number(self):
        """Generate unique slip number"""
        import uuid
        return f"PS{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

class Holiday(models.Model):
    """Doctor holidays and unavailability"""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holidays')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    is_recurring = models.BooleanField(default=False)  # For yearly holidays
    
    class Meta:
        ordering = ['start_date']
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.start_date} to {self.end_date}"
