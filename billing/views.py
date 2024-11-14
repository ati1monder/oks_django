from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from datetime import timedelta
from liqpay.liqpay3 import LiqPay
import urllib.parse
import random
from django.core.mail import send_mail
import pytz
from babel.dates import format_datetime
from datetime import datetime
from django.utils.timezone import make_aware
import logging
import base64
import json
logger = logging.getLogger(__name__)
from adminpanel import models

# Create your views here.

def check_request(request, *parameters) -> HttpResponse | None:
    for p in parameters:
        if request.GET.get(p) is None or request.GET.get(p) == '':
            return HttpResponse(f'Ви не вказали "{p}" в URL.')
    return None

def create_payment(request, type, input_id: int | str):
    template_name = 'billing/pay.html'

    # checking if query parameters exist
    if type == 0 or type == 1: # online and offline meetings
        check = check_request(request, 'name', 'surname', 'email', 'number')
        if check:
            return check
        logger.debug(f"Request GET data: {request.GET}")
        name = request.GET.get('name')
        surname = request.GET.get('surname')
        email = request.GET.get('email')
        number = request.GET.get('number')
        if request.GET.get('time_zone'):
            time_zone = request.GET.get('time_zone')
        if request.GET.get('nop'): # getting number of participants for offline meeting
            nop = int(request.GET.get('nop'))

        if not request.GET.get('nop') and type == 0: # testing if number of participants is not none if offline meeting
            return HttpResponse('Ви не вказали "nop" (number of participants) в URL.')
        
        if type == 1:
            check = check_request(request, 'time_zone')
            if check:
                return check
        
    if type == 2: # subscription
        check = check_request(request, 'id')
        if check:
            return check
        user_id = request.GET.get('id')


    # liqpay billing
    if type == 0: # offline meeting
        meeting_id_int = int(input_id)
        description = f'Оплата для офлайн зустрічі (ID: {meeting_id_int})'
        object = get_object_or_404(models.OfflineClassesModel, pk=meeting_id_int)
        if object.current_participants >= object.max_participants or object.current_participants + nop > object.max_participants:
            return HttpResponse(f'Перевищено допустиму кількість max_participants ({nop} + {object.current_participants} > {object.max_participants}).')
        count = models.OfflineClassRegistrationModel.objects.count() + 1
        sale_object = models.OfflineClassSale.objects.get(pk=1)
        price = object.price * nop
        if sale_object.due_to >= timezone.datetime.now().date() and sale_object.is_enabled == True:
            price = price * sale_object.coefficient
        query_params = {
            'class_id': meeting_id_int,
            'name': name,
            'surname': surname,
            'email': email,
            'number': number,
            'type': type,
            'nop': nop
        }
    if type == 1: # online meetings
        meeting_ids_list = list(map(int, input_id.split(',')))
        object_arr = []
        description = f'Оплата для онлайн зустрічі (ID: {meeting_ids_list})'
        for object_id in meeting_ids_list:
            object_arr.append(get_object_or_404(models.OnlineClassesModel, pk=object_id))
        count = models.OnlineClassRegistrationModel.objects.count() + 1
        price = 0
        for object_meeting in object_arr:
            price += object_meeting.price
        sale_object = models.OnlineClassSale.objects.get(pk=1)
        if sale_object.due_to >= timezone.datetime.now().date() and sale_object.is_enabled == True:
            price = price * sale_object.coefficient
        query_params = {
            'class_id': input_id,
            'name': name,
            'surname': surname,
            'email': email,
            'number': number,
            'type': type,
            'time_zone': time_zone
        }
    if type == 2: # subscription
        subscription = models.SubscriptionTypeModel.objects.get(pk=input_id)
        description = subscription.__str__()
        price = subscription.price
        count = models.GlobalUserModel.objects.count()
        query_params = {
            'user_id': user_id,
            'subscription_id': input_id,
            'type': type
        }

    # liqpay widget forming
    encoded_query_params = urllib.parse.urlencode(query_params)
    url = f'{settings.BILLING_IP}/billing/pay-callback/?{encoded_query_params}'

    liqpay = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)
    params = {
        'action': 'pay',
        'amount': price,
        'currency': 'UAH',
        'description': description,
        'order_id': f'order_number{count}_type{type}_random{random.randint(1, 100)}',
        'version': '3',
        'sandbox': 1,
        'server_url': url,
    }
    signature = liqpay.cnb_signature(params)
    data = liqpay.cnb_data(params)

    return render(request, template_name, {'signature': signature, 'data': data})


@method_decorator(csrf_exempt, name='dispatch')
class PayCallbackView(View): # callback for liqpay success payment
    def post(self, request, *args, **kwargs):
        print(request.GET)
        type = int(request.GET.get('type'))
        if type == 0 or type == 1: # checking query parameters for offline and online meetings
            class_id = request.GET.get('class_id')
            name = request.GET.get('name')
            surname = request.GET.get('surname')
            email = request.GET.get('email')
            number = request.GET.get('number')
            if type == 1:
                time_zone = request.GET.get('time_zone')



        if request.GET.get('nop'): # number of participants for offline meeting
            nop = int(request.GET.get('nop'))
        if type == 2: # checking query parameters for a subscription
            subscription_id = int(request.GET.get('subscription_id'))
            user_id = int(request.GET.get('user_id'))

        # forming liqpay object to test signature
        liqpay = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)

        data = request.POST.get('data')
        if not data:
            return HttpResponse('Немає data', status=400)
        decoded_data = base64.b64decode(data).decode('utf-8')
        data_dict = json.loads(decoded_data)

        signature = request.POST.get('signature')
        sign = liqpay.str_to_sign(settings.LIQPAY_PRIVATE_KEY + data + settings.LIQPAY_PRIVATE_KEY)
        if sign == signature:
            if data_dict['status']:
                if data_dict['status'] == "failure" or data_dict['status'] == "error":
                    return HttpResponse(status=200)
            classes = []
            if type == 0: # success handling for offline meeting
                models.OfflineClassRegistrationModel.objects.create(class_id=models.OfflineClassesModel.objects.get(pk=class_id), user_name=name, email=email, user_surname=surname, number=number, number_of_participants=nop)
                offline_class = get_object_or_404(models.OfflineClassesModel, pk=class_id)
                offline_class.current_participants += nop
                offline_class.save()
                send_mail(
                    'Інформація про офлайн мітинг OXYOGA',
                    f'Намасте, {name}.\n.Ви успішно зареєструвались на офлайн заняття OXYOGA. Обрана зустріч: {offline_class.class_name}. \n '
                    f'Місце проведення: {models.OfflineClassesModel.objects.get(pk=class_id).location}.\n Дата та час '
                    f'початку: {models.OfflineClassesModel.objects.get(pk=class_id).start_date} '
                    f'{models.OfflineClassesModel.objects.get(pk=class_id).start_time}.\nДякуємо за участь!',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                send_mail(
                    'Хтось зареєструвався на ваше офлайн заняття',
                    f'Аня, вітаю. Користувач {name} {surname} зареєструвався на ваше офлайн заняття "{offline_class.class_name}", Заплановане на {offline_class.start_date} {offline_class.start_time}.',
                    'from@example.com',
                    ['oximec12@gmail.com'],
                    fail_silently=False,
                )
            
            if type == 1:  # success handling for online meetings
                meeting_ids_list = list(map(int, class_id.split(',')))
                for m_id in meeting_ids_list:
                    class_instance = models.OnlineClassesModel.objects.get(pk=m_id)
                    classes.append(class_instance)
                    models.OnlineClassRegistrationModel.objects.create(class_id=class_instance, user_name=name, email=email, user_surname=surname, number=number)
                links = ''
                for class_instance in classes:
                    link = class_instance.zoom_link
                    start_date = class_instance.start_date
                    start_time = class_instance.start_time

                    # Convert start_date and start_time to datetime
                    start_datetime = make_aware(datetime.combine(start_date, start_time))

                    # Convert to the specified time zone
                    tz = pytz.timezone(time_zone)
                    start_datetime_tz = start_datetime.astimezone(tz)

                    # Format the datetime with the time zone
                    formatted_time = format_datetime(start_datetime_tz, format="yyyy-MM-dd HH:mm zzzz", tzinfo=tz, locale='uk_UA')

                    links += f'Посилання на Zoom: {link}. Дата та час початку: {formatted_time}. \n'
                send_mail(
                    'Інформація про онлайн заняття OXYOGA',
                    f'Намасте, {name}.\nВи успішно зареєструвались на онлайн заняття OXYOGA. Обрані заняття:\n {links} \nДякуємо за участь!',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                send_mail(
                    'Хтось зареєструвався на ваше онлайн заняття',
                    f'Аня, вітаю. Користувач {name} зареєструвався на ваше/і онлайн заняття. Вибрані заннятя: \n"{links}"',
                    'from@example.com',
                    ['oximec12@gmail.com'],
                    fail_silently=False,
                )

            if type == 2: # success handling for subscriptions
                subscription = models.SubscriptionTypeModel.objects.get(pk=subscription_id)
                start_date = timezone.now()
                end_date = timezone.now() + timedelta(days=30*subscription.duration_in_months)
                try:
                    user = models.GlobalUserModel.objects.get(user=User.objects.get(pk=user_id))
                    user.subscription_type = subscription
                    user.subscription_start_date = start_date
                    user.subscription_end_date = end_date
                    user.money_spent += subscription.price
                    user.save()
                    send_mail(
                        'Хтось придбав підписку на вашому сайті',
                        f'Аня, вітаю. Користувач {user.user.first_name} {user.user.last_name} придбав підписку на вашому сайті. Початок підписки: {start_date}. Кінець підписки: {end_date}.',
                        'from@example.com',
                        ['oximec12@gmail.com'],
                        fail_silently=False,
                    )
                except models.GlobalUserModel.DoesNotExist:
                    user = models.GlobalUserModel.objects.create(user=User.objects.get(pk=user_id), subscription_type=subscription, subscription_start_date=start_date, subscription_end_date = end_date, money_spent=subscription.price)

        return HttpResponse(status=200)