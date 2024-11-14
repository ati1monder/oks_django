from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import timedelta
from adminpanel import models
from django.utils.timezone import make_aware, datetime
from django.utils import timezone
import pytz

@shared_task
def send_meeting_reminders():
    now = datetime.now()
    now_aware = make_aware(now.replace(second=0, microsecond=0))
    time_threshold = now_aware + timedelta(minutes=30)
    upcoming_meetings = models.OnlineClassesModel.objects.filter(
        start_date=time_threshold.date(),
        start_time=time_threshold.time(),
        reminder_sent=False
    )
    for meeting in upcoming_meetings:
        link = meeting.zoom_link
        send_mail(
            'Нагадування про заняття OXYOGA',
            f'Намасте, {user.first_name}! Ви записані на {class_item.class_name}. \nДата: {meeting.start_date} о {meeting.start_time}. \nПосилання на заняття: {link}',
            'from@example.com',
            [reg.email for reg in models.OnlineClassRegistrationModel.objects.filter(class_id=meeting.id)],
            fail_silently=False,
        )
        meeting.reminder_sent = True
        meeting.save()
##
def send_subscription_expiration_reminders():
    kyiv_tz = pytz.timezone('Europe/Kiev')
    tomorrow = timezone.now().astimezone(kyiv_tz).date() + timedelta(days=1)
    expiring_subscriptions = models.GlobalUserModel.objects.filter(subscription_end_date=tomorrow)
    for subscription in expiring_subscriptions:
        user = subscription.user
        #TODO: better email template
        send_mail(
            'Нагадування про закінчення підписки на OXYOGA',
            f'Намасте, {user.first_name}! Ваша підписка на відео закінчиться {subscription.subscription_end_date}. \nПісля закінчення поновіть доступ у своєму особистому кабінеті.',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )