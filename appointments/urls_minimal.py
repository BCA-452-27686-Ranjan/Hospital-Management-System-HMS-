from django.urls import path
from . import views_booking_payment

app_name = 'appointments'

urlpatterns = [
    # Booking with Payment URLs
    path('book-with-payment/', views_booking_payment.book_appointment_with_payment, name='book_appointment_with_payment'),
    path('process-booking-payment/<int:payment_id>/', views_booking_payment.process_booking_payment, name='process_booking_payment'),
    path('confirm-booking-payment/<int:payment_id>/', views_booking_payment.confirm_booking_payment, name='confirm_booking_payment'),
    path('booking-payment-slip/<int:slip_id>/', views_booking_payment.booking_payment_slip, name='booking_payment_slip'),
]
