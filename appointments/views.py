from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import get_template
from .models import Appointment, MedicalRecord, PatientFeedback, PaymentSlip
from .forms import AppointmentBookingForm, MockPaymentForm, MedicalRecordForm, DoctorConfirmationForm
from accounts.models import PatientProfile, DoctorProfile, MedicalReport

User = get_user_model()

def generate_payment_slip(appointment, payment_method, transaction_id):
    """Generate payment slip for appointment"""
    try:
        # Create payment slip record
        payment_slip = PaymentSlip.objects.create(
            appointment=appointment,
            slip_number=f"PS{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}",
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=appointment.payment_amount,
            payment_date=timezone.now(),
            patient_name=appointment.patient.get_full_name(),
            doctor_name=appointment.doctor.get_full_name(),
            consultation_fee=appointment.payment_amount,
            status='PAID'
        )
        
        # Generate PDF slip
        pdf_content = generate_payment_slip_pdf(payment_slip)
        
        # Save PDF file
        from django.core.files.base import ContentFile
        filename = f"payment_slip_{payment_slip.slip_number}.pdf"
        payment_slip.slip_file.save(filename, ContentFile(pdf_content))
        
        return payment_slip
        
    except Exception as e:
        print(f"Error generating payment slip: {e}")
        return None

def generate_payment_slip_pdf(payment_slip):
    """Generate PDF for payment slip"""
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("PAYMENT SLIP", title_style))
        content.append(Spacer(1, 20))
        
        # Payment details table
        data = [
            ['Slip Number:', payment_slip.slip_number],
            ['Transaction ID:', payment_slip.transaction_id],
            ['Payment Date:', payment_slip.payment_date.strftime('%B %d, %Y at %I:%M %p')],
            ['Payment Method:', payment_slip.get_payment_method_display()],
            ['Amount:', f"₹{payment_slip.amount}"],
            ['Status:', payment_slip.status],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ]))
        
        content.append(table)
        content.append(Spacer(1, 20))
        
        # Patient and Doctor details
        content.append(Paragraph("Patient Details", heading_style))
        
        patient_data = [
            ['Name:', payment_slip.patient_name],
            ['Email:', payment_slip.appointment.patient_email],
            ['Phone:', payment_slip.appointment.patient_phone],
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        content.append(patient_table)
        content.append(Spacer(1, 20))
        
        content.append(Paragraph("Doctor Details", heading_style))
        
        doctor_data = [
            ['Name:', payment_slip.doctor_name],
            ['Consultation Fee:', f"₹{payment_slip.consultation_fee}"],
        ]
        
        doctor_table = Table(doctor_data, colWidths=[2*inch, 4*inch])
        doctor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        content.append(doctor_table)
        content.append(Spacer(1, 30))
        
        # Footer note
        content.append(Paragraph("This is a computer-generated payment slip. No signature required.", 
                              ParagraphStyle('Footer', fontSize=10, alignment=1)))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF content
        pdf_value = buffer.getvalue()
        buffer.close()
        
        return pdf_value
        
    except ImportError:
        # Fallback if reportlab is not available
        print("ReportLab not available for PDF generation")
        return b"Payment slip PDF generation not available"
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return b"Error generating payment slip PDF"

@login_required
def manage_schedule(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('dashboard:home')
    
    doctor = request.user
    
    # Get existing schedules
    schedules = Schedule.objects.filter(doctor=doctor).order_by('day_of_week')
    
    # Get upcoming holidays
    holidays = Holiday.objects.filter(
        doctor=doctor,
        end_date__gte=timezone.now().date()
    ).order_by('start_date')
    
    context = {
        'schedules': schedules,
        'holidays': holidays,
    }
    
    return render(request, 'appointments/manage_schedule.html', context)

@login_required
def add_schedule(request):
    if request.user.role != 'DOCTOR':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        day_of_week = int(request.POST.get('day_of_week'))
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        max_patients = int(request.POST.get('max_patients', 10))
        
        # Validate time
        if start_time >= end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        # Create or update schedule
        schedule, created = Schedule.objects.update_or_create(
            doctor=request.user,
            day_of_week=day_of_week,
            defaults={
                'start_time': start_time,
                'end_time': end_time,
                'max_patients_per_day': max_patients,
                'is_active': True
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Schedule added successfully',
            'schedule': {
                'day_of_week': schedule.get_day_of_week_display(),
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'max_patients': schedule.max_patients_per_day
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_holiday(request):
    if request.user.role != 'DOCTOR':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')
        is_recurring = request.POST.get('is_recurring') == 'on'
        
        # Validate dates
        if start_date > end_date:
            return JsonResponse({'error': 'End date must be after start date'}, status=400)
        
        holiday = Holiday.objects.create(
            doctor=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            is_recurring=is_recurring
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Holiday added successfully',
            'holiday': {
                'start_date': holiday.start_date.strftime('%Y-%m-%d'),
                'end_date': holiday.end_date.strftime('%Y-%m-%d'),
                'reason': holiday.reason,
                'is_recurring': holiday.is_recurring
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_available_slots(request):
    """API endpoint to get available appointment slots for a doctor"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    
    if not doctor_id or not date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        doctor = User.objects.get(pk=doctor_id, role='DOCTOR')
        target_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get doctor's schedule for that day
        day_of_week = target_date.weekday()
        schedule = Schedule.objects.filter(doctor=doctor, day_of_week=day_of_week, is_active=True).first()
        
        if not schedule:
            return JsonResponse({'slots': []})
        
        # Check if doctor is on holiday
        is_holiday = Holiday.objects.filter(
            doctor=doctor,
            start_date__lte=target_date,
            end_date__gte=target_date
        ).exists()
        
        if is_holiday:
            return JsonResponse({'slots': []})
        
        # Get existing appointments for that day
        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date=target_date,
            status__in=['SCHEDULED', 'PENDING']
        )
        
        # Generate time slots (30-minute intervals)
        slots = []
        current_time = timezone.datetime.combine(target_date, schedule.start_time)
        end_time = timezone.datetime.combine(target_date, schedule.end_time)
        
        while current_time < end_time:
            slot_time = current_time.time()
            slot_datetime = timezone.datetime.combine(target_date, slot_time)
            
            # Check if slot is available
            is_available = True
            for apt in existing_appointments:
                apt_time = apt.appointment_date.time()
                # Check if slot conflicts with existing appointment (within 30 minutes)
                time_diff = abs((timezone.datetime.combine(target_date, slot_time) - 
                                timezone.datetime.combine(target_date, apt_time)).total_seconds() / 60)
                if time_diff < 30:
                    is_available = False
                    break
            
            if is_available:
                slots.append({
                    'time': slot_time.strftime('%H:%M'),
                    'datetime': slot_datetime.strftime('%Y-%m-%d %H:%M'),
                    'available': True
                })
            
            current_time += timezone.timedelta(minutes=30)
        
        return JsonResponse({'slots': slots})
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def book_appointment(request):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('dashboard:home')
    
    # Get patient profile
    try:
        patient_profile = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        patient_profile = PatientProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Handle medical report upload
            report_file = request.FILES.get('report_file')
            if report_file:
                try:
                    medical_report = MedicalReport.objects.create(
                        patient=patient_profile,
                        title=report_file.name,
                        report_file=report_file,
                        uploaded_by=request.user
                    )
                    messages.success(request, "Medical report uploaded successfully!")
                except Exception as e:
                    messages.error(request, f"Error uploading medical report: {str(e)}")
            
            # Store form data in session for later use after payment
            appointment_data = {
                'doctor_id': form.cleaned_data['doctor'].id,
                'patient_name': form.cleaned_data['patient_name'],
                'patient_age': form.cleaned_data['patient_age'],
                'patient_address': form.cleaned_data.get('patient_address', ''),
                'patient_phone': form.cleaned_data['patient_phone'],
                'patient_email': form.cleaned_data.get('patient_email', ''),
                'reason': form.cleaned_data['reason'],
                'priority': form.cleaned_data['priority'],
                'notification_preference': form.cleaned_data.get('notification_preference', 'EMAIL'),
                'payment_option': 'pay_now'
            }
            
            # Add medical report ID if uploaded
            if report_file and 'medical_report' in locals():
                appointment_data['medical_report_id'] = medical_report.id
            
            request.session['pending_appointment'] = appointment_data
            
            # Get consultation fee for display
            doctor = form.cleaned_data['doctor']
            consultation_fee = 500  # Default fee
            if hasattr(doctor, 'doctor_profile') and doctor.doctor_profile.consultation_fee:
                consultation_fee = doctor.doctor_profile.consultation_fee
            
            # Store fee in session
            request.session['pending_consultation_fee'] = float(consultation_fee)
            
            # Return JSON response for AJAX request to show payment modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'show_payment': True,
                    'consultation_fee': consultation_fee,
                    'doctor_name': doctor.get_full_name() or doctor.username,
                    'appointment_summary': {
                        'patient_name': appointment_data['patient_name'],
                        'reason': appointment_data['reason'],
                        'priority': appointment_data['priority']
                    }
                })
            
            # For regular form submission, redirect to payment page
            return redirect('appointments:process_payment')
            
    else:
        form = AppointmentBookingForm(user=request.user)
    
    # Get patient's medical reports
    medical_reports = MedicalReport.objects.filter(patient=patient_profile).order_by('-uploaded_at')
    
    return render(request, 'appointments/book_appointment.html', {
        'form': form,
        'medical_reports': medical_reports
    })

@login_required
def process_payment(request):
    """Process payment for pending appointment (appointment not created yet)"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can make payments.')
        return redirect('dashboard:home')
    
    # Get pending appointment data from session
    pending_data = request.session.get('pending_appointment')
    if not pending_data:
        messages.error(request, 'No pending appointment found. Please start the booking process again.')
        return redirect('appointments:book_appointment')
    
    consultation_fee = request.session.get('pending_consultation_fee', 500)
    
    if request.method == 'POST':
        form = MockPaymentForm(request.POST)
        
        if form.is_valid():
            # Get payment details
            payment_method = form.cleaned_data['payment_method']
            
            # Generate mock transaction ID
            import uuid
            transaction_id = f"MOCK_{uuid.uuid4().hex[:12].upper()}"
            
            # NOW create the appointment (only after successful payment)
            try:
                doctor = User.objects.get(id=pending_data['doctor_id'])
                
                # Create the appointment
                appointment = Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    patient_name=pending_data['patient_name'],
                    patient_age=pending_data['patient_age'],
                    patient_address=pending_data.get('patient_address', ''),
                    patient_phone=pending_data['patient_phone'],
                    patient_email=pending_data.get('patient_email', ''),
                    reason=pending_data['reason'],
                    priority=pending_data['priority'],
                    notification_preference=pending_data.get('notification_preference', 'EMAIL'),
                    status='SCHEDULED',  # Status is SCHEDULED after payment
                    payment_status='SUCCESSFUL',
                    payment_method=payment_method,
                    payment_transaction_id=transaction_id,
                    payment_amount=consultation_fee,
                    paid_at=timezone.now()
                )
                
                # Link medical report if uploaded
                medical_report_id = pending_data.get('medical_report_id')
                if medical_report_id:
                    try:
                        medical_report = MedicalReport.objects.get(id=medical_report_id)
                        appointment.medical_reports.add(medical_report)
                    except MedicalReport.DoesNotExist:
                        pass
                
                # Clear session data
                if 'pending_appointment' in request.session:
                    del request.session['pending_appointment']
                if 'pending_consultation_fee' in request.session:
                    del request.session['pending_consultation_fee']
                
                # Generate payment slip
                payment_slip = generate_payment_slip(appointment, payment_method, transaction_id)
                
                messages.success(request, 'Payment processed successfully! Your appointment has been booked.')
                return redirect('appointments:payment_confirmation', appointment.id)
                
            except User.DoesNotExist:
                messages.error(request, 'Doctor not found. Please try booking again.')
                return redirect('appointments:book_appointment')
            except Exception as e:
                messages.error(request, f'Error creating appointment: {str(e)}')
                return redirect('appointments:book_appointment')
    else:
        form = MockPaymentForm()
    
    # Get doctor info for display
    try:
        doctor = User.objects.get(id=pending_data['doctor_id'])
        doctor_name = doctor.get_full_name() or doctor.username
    except:
        doctor_name = "Doctor"
    
    context = {
        'form': form,
        'consultation_fee': consultation_fee,
        'doctor_name': doctor_name,
        'appointment_summary': {
            'patient_name': pending_data['patient_name'],
            'reason': pending_data['reason'],
            'priority': pending_data['priority']
        },
        'is_popup': request.GET.get('popup', False)
    }
    
    return render(request, 'appointments/process_payment.html', context)

@login_required
def mock_payment(request, appointment_id):
    """Mock payment view for appointments"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can make payments.')
        return redirect('dashboard:home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    if appointment.payment_status == 'SUCCESSFUL':
        messages.info(request, 'Payment has already been completed for this appointment.')
        return redirect('appointments:payment_confirmation', appointment_id)
    
    if request.method == 'POST':
        form = MockPaymentForm(request.POST)
        
        if form.is_valid():
            # Mock payment processing
            payment_method = form.cleaned_data['payment_method']
            
            # Generate mock transaction ID
            import uuid
            transaction_id = f"MOCK_{uuid.uuid4().hex[:12].upper()}"
            
            # Update appointment with payment details
            appointment.payment_method = payment_method
            appointment.payment_status = 'SUCCESSFUL'
            appointment.payment_transaction_id = transaction_id
            appointment.paid_at = timezone.now()
            
            # Set payment amount (mock consultation fee)
            if hasattr(appointment.doctor, 'doctor_profile') and appointment.doctor.doctor_profile.consultation_fee:
                appointment.payment_amount = appointment.doctor.doctor_profile.consultation_fee
            else:
                appointment.payment_amount = 500  # Default mock amount
            
            # Update appointment status
            if appointment.status == 'PENDING_PAYMENT':
                appointment.status = 'SCHEDULED'
            
            appointment.save()
            
            # Generate payment slip
            payment_slip = generate_payment_slip(appointment, payment_method, transaction_id)
            
            messages.success(request, 'Payment processed successfully!')
            return redirect('appointments:payment_confirmation', appointment.id)
    else:
        form = MockPaymentForm()
    
    # Get consultation fee
    consultation_fee = 500  # Default fee
    if hasattr(appointment.doctor, 'doctor_profile') and appointment.doctor.doctor_profile.consultation_fee:
        consultation_fee = appointment.doctor.doctor_profile.consultation_fee
    
    context = {
        'appointment': appointment,
        'form': form,
        'consultation_fee': consultation_fee,
    }
    
    return render(request, 'appointments/mock_payment.html', context)

@login_required
def payment_confirmation(request, appointment_id):
    """Payment confirmation page"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Only allow access if user is patient, doctor, or admin
    if request.user.role not in ['PATIENT', 'DOCTOR', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    # Patients can only see their own appointments
    if request.user.role == 'PATIENT' and appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    # Doctors can only see their own appointments
    if request.user.role == 'DOCTOR' and appointment.doctor != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'appointments/payment_confirmation.html', context)

@login_required
def book_with_payment_later(request, appointment_id):
    """Book appointment with payment to be made later"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('dashboard:home')
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, user=request.user)
        payment_option = request.POST.get('payment_option', 'pay_later')
        
        if form.is_valid():
            # Handle medical report upload
            report_file = request.FILES.get('report_file')
            if report_file:
                try:
                    medical_report = MedicalReport.objects.create(
                        patient=patient_profile,
                        title=report_file.name,
                        report_file=report_file,
                        uploaded_by=request.user
                    )
                    messages.success(request, "Medical report uploaded successfully!")
                except Exception as e:
                    messages.error(request, f"Error uploading medical report: {str(e)}")
            
            # Save appointment
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'PENDING'
            appointment.payment_status = 'PENDING'
            appointment.save()  # CRITICAL: Save to database!
            
            # Link medical report if uploaded
            if report_file and 'medical_report' in locals():
                appointment.medical_reports.add(medical_report)
                messages.success(request, "Medical report linked to appointment successfully!")
            
            messages.success(request, f'Appointment booked successfully{" for " + appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p") if appointment.appointment_date else ""}! Your appointment will be confirmed by the doctor. Please be ready to make payment at the appointment time.')
            return redirect('appointments:appointment_detail', pk=appointment.pk)
    else:
        form = AppointmentBookingForm(user=request.user)
    
    # Get patient's medical reports
    try:
        patient_profile = request.user.patient_profile
        medical_reports = MedicalReport.objects.filter(patient=patient_profile).order_by('-uploaded_at')
    except PatientProfile.DoesNotExist:
        medical_reports = MedicalReport.objects.none()
    
    return render(request, 'appointments/book_appointment.html', {
        'form': form,
        'medical_reports': medical_reports,
    })

@login_required
def print_payment_slip(request, appointment_id):
    """Print payment slip for appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Only allow access if user is patient, doctor, or admin
    if request.user.role not in ['PATIENT', 'DOCTOR', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    # Patients can only print their own appointments
    if request.user.role == 'PATIENT' and appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    # Doctors can only print their own appointments
    if request.user.role == 'DOCTOR' and appointment.doctor != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    # Check if payment slip exists
    if not appointment.payment_slip:
        messages.error(request, 'Payment slip not found for this appointment.')
        return redirect('appointments:appointment_detail', pk=appointment_id)
    
    # Check if payment slip file exists
    if not appointment.payment_slip.slip_file:
        messages.error(request, 'Payment slip file not available.')
        return redirect('appointments:appointment_detail', pk=appointment_id)
    
    # Generate print-friendly HTML
    context = {
        'appointment': appointment,
        'payment_slip': appointment.payment_slip,
    }
    
    return render(request, 'appointments/print_payment_slip.html', context)

@login_required
def update_patient_report(request, appointment_id):
    """Update patient report for completed appointments"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Only doctors can update patient reports.')
        return redirect('dashboard:home')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if appointment.doctor != request.user:
        messages.error(request, 'You can only update reports for your own appointments.')
        return redirect('appointments:my_appointments')
    
    if appointment.status != 'COMPLETED':
        messages.error(request, 'Patient reports can only be updated for completed appointments.')
        return redirect('appointments:appointment_detail', pk=appointment.pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            # Update existing medical record or create new one
            if hasattr(appointment, 'medical_record'):
                medical_record = appointment.medical_record
                medical_record.diagnosis = form.cleaned_data['diagnosis']
                medical_record.symptoms = form.cleaned_data['symptoms']
                medical_record.treatment = form.cleaned_data['treatment']
                medical_record.prescription = form.cleaned_data['prescription']
                medical_record.save()
                messages.success(request, 'Patient report updated successfully!')
            else:
                medical_record = form.save(commit=False)
                medical_record.patient = appointment.patient
                medical_record.doctor = appointment.doctor
                medical_record.appointment = appointment
                medical_record.save()
                messages.success(request, 'Patient report created successfully!')
            
            return redirect('appointments:appointment_detail', pk=appointment.pk)
    else:
        # Pre-populate form with existing data if medical record exists
        if hasattr(appointment, 'medical_record'):
            form = MedicalRecordForm(instance=appointment.medical_record)
        else:
            form = MedicalRecordForm()
    
    return render(request, 'appointments/update_patient_report.html', {
        'form': form,
        'appointment': appointment
    })

def feedback_form(request, appointment_id):
    """Submit feedback for completed appointments"""
    # Check authentication manually
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can submit feedback.')
        return redirect('dashboard:home')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if appointment.patient != request.user:
        messages.error(request, 'You can only submit feedback for your own appointments.')
        return redirect('appointments:my_appointments')
    
    if appointment.status != 'COMPLETED':
        messages.error(request, 'Feedback can only be submitted for completed appointments.')
        return redirect('appointments:appointment_detail', pk=appointment.pk)
    
    if hasattr(appointment, 'feedback'):
        messages.error(request, 'You have already submitted feedback for this appointment.')
        return redirect('appointments:appointment_detail', pk=appointment.pk)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comments = request.POST.get('comments', '')
        would_recommend = request.POST.get('would_recommend') == 'on'
        
        if rating:
            feedback = PatientFeedback.objects.create(
                appointment=appointment,
                patient=appointment.patient,
                doctor=appointment.doctor,
                rating=int(rating),
                comments=comments,
                would_recommend=would_recommend
            )
            messages.success(request, 'Thank you for your feedback!')
            return redirect('appointments:appointment_detail', pk=appointment.pk)
        else:
            messages.error(request, 'Please select a rating.')
    
    return render(request, 'appointments/submit_feedback.html', {
        'appointment': appointment
    })

@login_required
def delete_medical_report_booking(request, report_id):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can delete their medical reports.')
        return redirect('appointments:book_appointment')
    
    try:
        patient_profile = request.user.patient_profile
        report = get_object_or_404(MedicalReport, id=report_id, patient=patient_profile)
        
        # Delete the file
        if report.report_file:
            report.report_file.delete()
        
        # Delete the record
        report.delete()
        messages.success(request, 'Medical report deleted successfully!')
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile setup first.')
    
    return redirect('appointments:book_appointment')

@login_required
def my_appointments(request):
    user = request.user
    
    if user.role == 'PATIENT':
        appointments = Appointment.objects.filter(patient=user).order_by('-appointment_date')
    elif user.role == 'DOCTOR':
        appointments = Appointment.objects.filter(doctor=user).order_by('-appointment_date')
    else:
        appointments = Appointment.objects.all().order_by('-appointment_date')
    
    # Search and filter
    search = request.GET.get('search')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
        
    if search:
        appointments = appointments.filter(
            Q(patient_name__icontains=search) |
            Q(patient_email__icontains=search)
        )
    if status:
        appointments = appointments.filter(status=status)
    if priority:
        appointments = appointments.filter(priority=priority)
    if date_from:
        appointments = appointments.filter(appointment_date__date__gte=date_from)
    if date_to:
        appointments = appointments.filter(appointment_date__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'is_doctor': user.role == 'DOCTOR',
    }
    
    return render(request, 'appointments/my_appointments.html', context)

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if request.user.role == 'PATIENT' and appointment.patient != request.user:
        messages.error(request, 'You can only view your own appointments.')
        return redirect('appointments:my_appointments')
    elif request.user.role == 'DOCTOR' and appointment.doctor != request.user:
        messages.error(request, 'You can only view your assigned appointments.')
        return redirect('appointments:my_appointments')
    
    # Get medical record if exists
    medical_record = getattr(appointment, 'medical_record', None)
    feedback = getattr(appointment, 'feedback', None)
    
    # Get medical reports for this appointment (for doctors to see)
    medical_reports = []
    if request.user.role == 'DOCTOR':
        try:
            patient_profile = appointment.patient.patient_profile
            # Get all medical reports for this patient (remove date filter for now)
            medical_reports = MedicalReport.objects.filter(
                patient=patient_profile
            ).order_by('-uploaded_at')
        except PatientProfile.DoesNotExist:
            medical_reports = []
    
    context = {
        'appointment': appointment,
        'medical_record': medical_record,
        'feedback': feedback,
        'medical_reports': medical_reports,
    }
    
    return render(request, 'appointments/appointment_detail.html', context)

@login_required
def confirm_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.user.role != 'DOCTOR' or appointment.doctor != request.user:
        messages.error(request, 'Only the assigned doctor can confirm appointments.')
        return redirect('appointments:my_appointments')
    
    if request.method == 'POST':
        form = DoctorConfirmationForm(request.POST, instance=appointment)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Appointment {appointment.get_status_display().lower()} successfully!')
            
            # Create medical record if appointment is completed
            if form.cleaned_data['status'] == 'COMPLETED':
                if not hasattr(appointment, 'medical_record'):
                    MedicalRecord.objects.create(
                        patient=appointment.patient,
                        doctor=appointment.doctor,
                        appointment=appointment,
                        diagnosis='To be updated',
                        symptoms='To be updated',
                        treatment='To be updated'
                    )
            
            return redirect('appointments:appointment_detail', pk=appointment.pk)
    else:
        form = DoctorConfirmationForm(instance=appointment)
    
    return render(request, 'appointments/confirm_appointment.html', {
        'form': form,
        'appointment': appointment
    })


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    can_cancel = False
    if request.user.role == 'PATIENT' and appointment.patient == request.user:
        can_cancel = appointment.can_cancel
    elif request.user.role == 'DOCTOR' and appointment.doctor == request.user:
        can_cancel = appointment.status in ['PENDING', 'SCHEDULED']
    elif request.user.role == 'ADMIN':
        can_cancel = True
    
    if not can_cancel:
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    return render(request, 'appointments/cancel_appointment.html', {'appointment': appointment})


@login_required
def doctor_dashboard(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('dashboard:home')
    
    doctor = request.user
    
    # Get appointment statistics
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__date=today
    )
    
    pending_appointments = Appointment.objects.filter(doctor=doctor, status='PENDING')
    scheduled_appointments = Appointment.objects.filter(doctor=doctor, status='SCHEDULED')
    completed_appointments = Appointment.objects.filter(doctor=doctor, status='COMPLETED')
    
    # Recent appointments
    recent_appointments = Appointment.objects.filter(doctor=doctor).order_by('-created_at')[:5]
    
    # Get patient feedback for this doctor
    recent_feedback = PatientFeedback.objects.filter(doctor=doctor).order_by('-created_at')[:5]
    feedback_count = PatientFeedback.objects.filter(doctor=doctor).count()
    
    # Calculate average rating
    from django.db.models import Avg
    avg_rating = PatientFeedback.objects.filter(doctor=doctor).aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'scheduled_appointments': scheduled_appointments,
        'completed_appointments': completed_appointments,
        'recent_appointments': recent_appointments,
        'recent_feedback': recent_feedback,
        'feedback_count': feedback_count,
        'average_rating': round(avg_rating, 1),
        'stats': {
            'today_count': today_appointments.count(),
            'pending_count': pending_appointments.count(),
            'scheduled_count': scheduled_appointments.count(),
            'completed_count': completed_appointments.count(),
        },
        # Direct counts for template compatibility
        'today_appointments_count': today_appointments.count(),
        'pending_appointments_count': pending_appointments.count(),
        'scheduled_appointments_count': scheduled_appointments.count(),
        'completed_appointments_count': completed_appointments.count(),
    }
    
    return render(request, 'appointments/doctor_dashboard.html', context)

@login_required
def patient_history(request, patient_id):
    if request.user.role not in ['DOCTOR', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    patient = get_object_or_404(User, pk=patient_id, role='PATIENT')
    
    # Filter appointments by patient and current doctor (unless admin)
    if request.user.role == 'ADMIN':
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
        medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')
    else:
        # For doctors, only show their own appointments with this patient
        appointments = Appointment.objects.filter(patient=patient, doctor=request.user).order_by('-appointment_date')
        medical_records = MedicalRecord.objects.filter(patient=patient, doctor=request.user).order_by('-created_at')
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    
    return render(request, 'appointments/patient_history.html', context)

@login_required
def patient_medical_reports(request, patient_id):
    if request.user.role not in ['DOCTOR', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    
    patient = get_object_or_404(User, pk=patient_id, role='PATIENT')
    
    try:
        patient_profile = patient.patient_profile
        medical_reports = MedicalReport.objects.filter(
            patient=patient_profile
        ).order_by('-uploaded_at')
        
        print(f"Found {medical_reports.count()} medical reports for patient {patient}")
        
    except PatientProfile.DoesNotExist:
        medical_reports = []
        messages.warning(request, 'Patient profile not found.')
    
    context = {
        'patient': patient,
        'medical_reports': medical_reports,
    }
    
    return render(request, 'appointments/patient_medical_reports.html', context)

@login_required
def create_medical_record(request, appointment_pk):
    appointment = get_object_or_404(Appointment, pk=appointment_pk)
    
    if request.user.role != 'DOCTOR' or appointment.doctor != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointments:appointment_detail', pk=appointment_pk)
    
    if hasattr(appointment, 'medical_record'):
        messages.info(request, 'Medical record already exists for this appointment.')
        return redirect('appointments:appointment_detail', pk=appointment_pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = appointment.patient
            medical_record.doctor = appointment.doctor
            medical_record.appointment = appointment
            medical_record.save()
            
            messages.success(request, 'Medical record created successfully.')
            return redirect('appointments:appointment_detail', pk=appointment_pk)
    else:
        form = MedicalRecordForm()
    
    return render(request, 'appointments/create_medical_record.html', {
        'form': form,
        'appointment': appointment
    })

@login_required
def submit_feedback(request, appointment_pk):
    appointment = get_object_or_404(Appointment, pk=appointment_pk)
    
    if request.user.role != 'PATIENT' or appointment.patient != request.user:
        messages.error(request, 'Access denied.')
        return redirect('appointments:appointment_detail', pk=appointment_pk)
    
    if appointment.status != 'COMPLETED':
        messages.error(request, 'Feedback can only be submitted for completed appointments.')
        return redirect('appointments:appointment_detail', pk=appointment_pk)
    
    if hasattr(appointment, 'feedback'):
        messages.info(request, 'Feedback already submitted for this appointment.')
        return redirect('appointments:appointment_detail', pk=appointment_pk)
    
    if request.method == 'POST':
        form = PatientFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.appointment = appointment
            feedback.patient = appointment.patient
            feedback.doctor = appointment.doctor
            feedback.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('appointments:appointment_detail', pk=appointment_pk)
    else:
        form = PatientFeedbackForm()
    
    return render(request, 'appointments/submit_feedback.html', {
        'form': form,
        'appointment': appointment
    })
