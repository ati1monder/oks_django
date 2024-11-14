from django.core.management.base import BaseCommand
from email_service.tasks import send_meeting_reminders

class Command(BaseCommand):
    help = 'Send meeting reminders'
#f
    def handle(self, *args, **kwargs):
        send_meeting_reminders()
        self.stdout.write(self.style.SUCCESS('Successfully sent meeting reminders'))