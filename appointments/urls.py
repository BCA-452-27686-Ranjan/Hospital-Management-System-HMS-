from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Original Booking URLs
    path('book/', views.book_appointment, name='book_appointment'),
    path('book/delete-report/<int:report_id>/', views.delete_medical_report_booking, name='delete_medical_report_booking'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointment/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/<int:appointment_pk>/create-medical-record/', views.create_medical_record, name='create_medical_record'),
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('manage-schedule/', views.manage_schedule, name='manage_schedule'),
    path('add-schedule/', views.add_schedule, name='add_schedule'),
    
    # Payment URLs
    path('process-payment/', views.process_payment, name='process_payment'),
    path('appointment/<int:appointment_id>/payment/', views.mock_payment, name='mock_payment'),
    path('appointment/<int:appointment_id>/payment-confirmation/', views.payment_confirmation, name='payment_confirmation'),
    path('appointment/<int:appointment_id>/print-payment-slip/', views.print_payment_slip, name='print_payment_slip'),
    path('appointment/<int:appointment_id>/book-with-payment-later/', views.book_with_payment_later, name='book_with_payment_later'),
    path('appointment/<int:appointment_id>/update-patient-report/', views.update_patient_report, name='update_patient_report'),
    path('appointment/<int:appointment_id>/submit-feedback/', views.feedback_form, name='submit_feedback'),
]
