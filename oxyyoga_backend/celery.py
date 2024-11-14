from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxyyoga_backend.settings')

app = Celery('oxyyoga_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-meeting-reminders-every-minute': {
        'task': 'email_service.tasks.send_meeting_reminders',  # Corrected task path
        'schedule': crontab(minute='*'),  # Runs every minute
    },
}