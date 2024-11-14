from django.core.management.base import BaseCommand
from email_service.tasks import send_subscription_expiration_reminders

class Command(BaseCommand):
    help = 'Send subscription expiration reminders'

    def handle(self, *args, **kwargs):
        send_subscription_expiration_reminders()
        self.stdout.write(self.style.SUCCESS('Successfully sent subscription expiration reminders'))