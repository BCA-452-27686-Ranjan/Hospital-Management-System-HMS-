from django.urls import path
from . import views
from . import views_payment
from . import views_booking_payment

app_name = 'appointments'

urlpatterns = [
    path('book/', views.book_appointment, name='book_appointment'),
    path('book-with-payment/', views_booking_payment.book_appointment_with_payment, name='book_appointment_with_payment'),
    path('process-booking-payment/<int:payment_id>/', views_booking_payment.process_booking_payment, name='process_booking_payment'),
    path('confirm-booking-payment/<int:payment_id>/', views_booking_payment.confirm_booking_payment, name='confirm_booking_payment'),
    path('booking-payment-slip/<int:slip_id>/', views_booking_payment.booking_payment_slip, name='booking_payment_slip'),
    path('book/delete-report/<int:report_id>/', views.delete_medical_report_booking, name='delete_medical_report_booking'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointment/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:pk>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('patient/<int:patient_id>/medical-reports/', views.patient_medical_reports, name='patient_medical_reports'),
    path('patient/<int:patient_id>/history/', views.patient_history, name='patient_history'),
    
    # Invoice URLs
    path('invoice/create/', views.create_invoice, name='create_invoice'),
    path('invoice/create/report/<int:report_id>/', views.create_invoice, name='create_invoice_report'),
    path('invoice/create/appointment/<int:appointment_id>/', views.create_invoice, name='create_invoice_appointment'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:pk>/traditional/', views.invoice_detail_traditional, name='invoice_detail_traditional'),
    path('invoice/list/', views.invoice_list, name='invoice_list'),
    path('invoice/<int:pk>/update/', views.update_invoice_status, name='update_invoice_status'),
    path('invoice/<int:pk>/mark-paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoice/<int:pk>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    
    # Payment URLs
    path('payment/invoice/<int:invoice_id>/', views_payment.make_payment, name='make_payment_invoice'),
    path('payment/appointment/<int:appointment_id>/', views_payment.make_payment, name='make_payment_appointment'),
    path('payment/process/<int:payment_id>/', views_payment.process_payment, name='process_payment'),
    path('payment/slip/<int:payment_id>/', views_payment.payment_slip, name='payment_slip'),
    path('payment/history/', views_payment.payment_history, name='payment_history'),
    path('payment/dashboard/', views_payment.doctor_payment_dashboard, name='doctor_payment_dashboard'),
    
    path('appointment/<int:appointment_pk>/medical-record/', views.create_medical_record, name='create_medical_record'),
    path('appointment/<int:appointment_pk>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Scheduling URLs
    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('schedule/add/', views.add_schedule, name='add_schedule'),
    path('schedule/holiday/add/', views.add_holiday, name='add_holiday'),
    path('api/available-slots/', views.get_available_slots, name='get_available_slots'),
    
    # Advanced Features URLs
    path('advanced-search/', views_advanced.advanced_search, name='advanced_search'),
    path('export/', views_advanced.export_appointments, name='export_appointments'),
    path('export/medical-records/', views_advanced.export_medical_records, name='export_medical_records'),
    path('analytics/', views_advanced.AppointmentAnalyticsView.as_view(), name='analytics'),
    path('user-management/', views_advanced.user_management, name='user_management'),
    path('system-logs/', views_advanced.system_logs, name='system_logs'),
    path('permission-denied/', views_advanced.permission_denied, name='permission_denied'),
]
