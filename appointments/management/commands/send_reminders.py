from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment

class Command(BaseCommand):
    help = 'Send appointment reminders to patients'

    def handle(self, *args, **options):
        # Get appointments scheduled for tomorrow (24 hours from now)
        tomorrow = timezone.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Find appointments for tomorrow that haven't had reminders sent
        appointments = Appointment.objects.filter(
            appointment_date__gte=tomorrow_start,
            appointment_date__lte=tomorrow_end,
            status='SCHEDULED',
            reminder_sent=False
        )
        
        sent_count = 0
        for appointment in appointments:
            try:
                appointment.send_reminder_email()
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reminder sent for appointment {appointment.id} - {appointment.patient_name}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder for appointment {appointment.id}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {sent_count} appointment reminders out of {appointments.count()} scheduled appointments'
            )
        )
