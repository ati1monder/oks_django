import requests
import base64
import random
import string

from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.utils import timezone
import datetime as dt
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.db.models import F
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import re
from . import models, forms

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def login_view(request):
    error_message = ''
    if request.user.is_authenticated:
        return redirect('admin_index')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'admin_index'
            return redirect(next_url)
        else:
            error_message = 'Invalid Credentials!'
    return render(request, 'adminpanel/login.html', {'error_message': error_message})

@login_required
@staff_member_required
def admin_index_view(request):
    return render(request, 'adminpanel/index.html')

def logout_view(request):
    logout(request)
    return redirect('admin_login')

@login_required
@staff_member_required
def user_view(request):
    users = get_user_model().objects.all()

    if request.GET.get('search_users'):
        users = users.filter(username__contains=request.GET.get('search_users'))

    user_details = []
    for user in users:
        try:
            global_user = models.GlobalUserModel.objects.get(user=user.id)
        except models.GlobalUserModel.DoesNotExist:
            global_user = None
        user_details.append({
            'user': user,
            'global_user': global_user,
        })
    paginator = Paginator(user_details, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'users': page_obj}
    return render(request, 'adminpanel/users.html', context)

@login_required
@staff_member_required
def user_details_view(request, userid):
    try:
        local_user = User.objects.get(pk=userid)
        user = models.GlobalUserModel.objects.get(user=local_user)
        phone_number = models.UserPhoneNumber.objects.get(user=local_user).phone_number_field
        is_global = True
    except models.GlobalUserModel.DoesNotExist:
        user = User.objects.get(pk=userid)
        phone_number = models.UserPhoneNumber.objects.get(user=user).phone_number_field
        is_global = False
    
    context = {
        'current_user': user,
        'is_global': is_global,
        'phone_number': phone_number
    }
    return render(request, 'adminpanel/user_details.html', context)

@login_required
@staff_member_required
def user_edit_view(request, userid):
    try:
        user = User.objects.get(pk=userid)
        global_user = models.GlobalUserModel.objects.get(user=user)
        is_global = True
    except models.GlobalUserModel.DoesNotExist:
        user = User.objects.get(pk=userid)
        is_global = False
        global_user = None
    
    if is_global:
        form = forms.GlobalUserForm(instance=global_user, user=user)
    else:
        form = forms.UserForm(instance=user)
    
    if request.method == "POST":
        if is_global:
            form = forms.GlobalUserForm(request.POST, instance=global_user, user=user)
        else:
            form = forms.UserForm(request.POST, instance=user)
        
        if form.is_valid():
            form.save()
            return redirect(reverse('users'))
        else:
            print(form.errors)

    if is_global:
        current_user = global_user
    else:
        current_user = user

    context = {
        'current_user': current_user,
        'is_global': is_global,
        'form': form
    }
    return render(request, 'adminpanel/user_edit.html', context)

@login_required
@staff_member_required
def user_new_subscription_view(request, userid):
    user = User.objects.get(pk=userid)
    if request.method == "POST":
        form = forms.NewUserSubscriptionForm(request.POST)
        if form.is_valid():
            sub_id = form.cleaned_data['subscription_type']
            sub_end_date = form.cleaned_data['subscription_end_date']
            models.GlobalUserModel.objects.create(user=user, 
                                                  subscription_type=sub_id, 
                                                  subscription_end_date=sub_end_date,
                                                  money_spent=0)
            
            return redirect(reverse('user_edit', args=[userid]))
    else:
        form = forms.NewUserSubscriptionForm()

    context = {
        'user': user,
        'form': form
    }
    return render(request, 'adminpanel/user_new_subscription.html', context)

@login_required
@staff_member_required
def user_delete_view(request, userid):
    user = User.objects.get(pk=userid)
    try:
        global_user = models.GlobalUserModel.objects.get(user=user)
        global_user.delete()
        user.delete()
    except models.GlobalUserModel.DoesNotExist:
        user.delete()
    
    return redirect('users')

@login_required
@staff_member_required
def courses_online_view(request):
    current_date = timezone.now().date()
    current_time = timezone.now().time()

    current_classes_list = models.OnlineClassesModel.objects.filter(start_date=current_date, start_time__gte=current_time).order_by('start_time')
    upcoming_classes_list = models.OnlineClassesModel.objects.filter(start_date__gt=current_date).order_by('start_date')
    previous_classes_list = models.OnlineClassesModel.objects.filter(start_date__lte=current_date).order_by('start_date')

    paginator_current = Paginator(current_classes_list, 5)
    paginator_upcoming = Paginator(upcoming_classes_list, 5)
    paginator_previous = Paginator(previous_classes_list, 5)

    page_number_current = request.GET.get('page_current') or 1
    page_number_upcoming = request.GET.get('page_upcoming') or 1
    page_number_previous = request.GET.get('page_previous') or 1

    current_classes = paginator_current.get_page(page_number_current)
    upcoming_classes = paginator_upcoming.get_page(page_number_upcoming)
    previous_classes = paginator_previous.get_page(page_number_previous)

    context = {
        'current_classes': current_classes,
        'upcoming_classes': upcoming_classes,
        'previous_classes': previous_classes,
        'token': request.session.get('zoom_access_token', ''),
        'type': 'online'
    }

    return render(request, 'adminpanel/courses.html', context)

@login_required
@staff_member_required
def course_online_details_view(request, classid):
    current_class = models.OnlineClassesModel.objects.get(pk=classid)
    registrations = models.OnlineClassRegistrationModel.objects.filter(class_id=current_class)
    context = {
        'class': models.OnlineClassesModel.objects.get(pk=classid),
        'registrations': registrations,
        'type': 'online'
    }
    return render(request, 'adminpanel/course_details.html', context)

@login_required
@staff_member_required
def course_online_delete(request, classid):
    try:
        class_item = models.OnlineClassesModel.objects.get(pk=classid)
        registrated_users = models.OnlineClassRegistrationModel.objects.filter(class_id=class_item)
        for user in registrated_users:
            send_mail(
                'Відміна онлайн заняття',
                f'Перепрошую за незручності, {user.user_name}. \nЗаняття {class_item.class_name} заплановане на {class_item.start_date} було відмінене. \nДля уточнення інформації зв\'яжіться зі мною.\nTelegram: t.me/oksymec \nЗ повагою, Анна Оксимець.',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
        class_item.delete()
        messages.success(request, 'Видалено успішно!')
    except models.OnlineClassesModel.DoesNotExist:
        messages.error(request, 'Клас не знайдено.')

    return redirect(reverse('courses_online'))


@login_required
@staff_member_required
def course_online_edit(request, classid):
    form = ''
    class_item = get_object_or_404(models.OnlineClassesModel, pk=classid)
    if request.method == "POST":
        form = forms.OnlineClassForm(request.POST, instance=class_item)
        if form.is_valid():
            for user in models.OnlineClassRegistrationModel.objects.filter(class_id=models.OnlineClassesModel.objects.get(pk=classid)):
                send_mail(
                    'Зміни в онлайн занятті',
                    f'Перепрошую за незручності, {user.user_name}. \nЗаняття {class_item.class_name} заплановане на {class_item.start_date} було змінено.\nНова дата та час зустрічі: {form.cleaned_data["start_date"]} {form.cleaned_data["start_time"]}. \nДля отримання додаткової інформації зв\'яжіться зі мною.\nTelegram: t.me/oksymec \nЗ повагою, Анна Оксимець.',
                    'from@example.com',
                    [user.email],
                    fail_silently=False
                )
            form.save()
            return redirect('courses_online')
    else:
        form = forms.OnlineClassForm(instance=class_item)
    context = {
        'form': form,
        'type': 'online'
    }
    return render(request, 'adminpanel/edit_course.html', context)

def google_login(request):
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    creds = None

    if os.path.exists(settings.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.CREDENTIALS_FILE, SCOPES)
            flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
            
            authorization_url, _ = flow.authorization_url(prompt='consent')

            request.session['authorization_url'] = authorization_url

            return redirect(authorization_url)
    
    return creds

def google_oauth_callback(request):
    authorization_response = request.get_full_path()

    flow = InstalledAppFlow.from_client_secrets_file(
        settings.CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar.events']
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials

    with open(settings.TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

    del request.session['authorization_url']

    return redirect('courses_online')

@login_required
@staff_member_required
def course_online_create(request):
    if request.method == 'POST':
        class_name = request.POST['class_name']
        description = request.POST['description']
        start_date = request.POST['start_date']
        start_time = request.POST['start_time']
        price = request.POST['price']
        duration = int(request.POST['time'])

        start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        zoom_datetime = str(timezone.make_aware(start_datetime, timezone.get_current_timezone()).isoformat())
        end_datetime = start_datetime + timedelta(minutes=duration)

        zoom_meeting = create_zoom_meeting(request, class_name, description, zoom_datetime, duration)
        zoom_link = zoom_meeting['join_url']

        creds = google_login(request)
        if isinstance(creds, HttpResponseRedirect):
            return creds

        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': 'ONLINE ' + class_name,
            'description': zoom_link,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Europe/Kiev',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/Kiev',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()

        models.OnlineClassesModel.objects.create(
            class_name=class_name, 
            description=description, 
            start_date=start_date, 
            start_time=start_time, 
            price=price, 
            zoom_link=zoom_link, 
            time=duration
        )

        messages.success(request, 'Заняття створено успішно!')
        return redirect('courses_online')
    else:
        form = forms.OnlineClassForm()
    
    context = {
        'form': form,
        'type': 'online'
    }
    return render(request, 'adminpanel/create_course.html', context)

@login_required
@staff_member_required
def course_online_create_future(request):
    if request.method == 'POST':
        form = forms.OnlineClassesFutureForm(request.POST)
        if form.is_valid():
            class_name = request.POST.get('class_name')
            description = request.POST.get('description')
            start_time = request.POST.get('start_time')
            duration = request.POST.get('duration')
            price = int(request.POST.get('price'))
            days_of_week_POST = [ int(i) for i in request.POST.getlist('days_of_week') ]
            number_of_months_POST = int(request.POST.get('number_of_months'))

            days = 30 * number_of_months_POST

            start_date = timezone.datetime.now().date()

            creds = google_login(request)
            if isinstance(creds, HttpResponseRedirect):
                return creds
            service = build('calendar', 'v3', credentials=creds)

            for i in range(days):
                current_date = start_date + timezone.timedelta(days=i)
                if current_date.weekday() in days_of_week_POST and not models.OnlineClassesModel.objects.filter(start_date=current_date, start_time=start_time).exists():
                    start_datetime = datetime.strptime(f"{current_date} {start_time}", '%Y-%m-%d %H:%M')
                    zoom_datetime = str(timezone.make_aware(start_datetime, timezone.get_current_timezone()).isoformat())

                    zoom_meeting = create_zoom_meeting(request, class_name, description, zoom_datetime, duration)
                    zoom_link = zoom_meeting['join_url']

                    start_datetime = datetime.strptime(f"{current_date} {start_time}", '%Y-%m-%d %H:%M')
                    end_datetime = start_datetime + timedelta(minutes=int(duration))

                    event = {
                        'summary': 'ONLINE ' + class_name,
                        'description': zoom_link,
                        'start': {
                            'dateTime': start_datetime.isoformat(),
                            'timeZone': 'Europe/Kiev',
                        },
                        'end': {
                            'dateTime': end_datetime.isoformat(),
                            'timeZone': 'Europe/Kiev',
                        },
                    }

                    event = service.events().insert(calendarId='primary', body=event).execute()

                    models.OnlineClassesModel.objects.create(class_name=class_name, 
                                                             description=description, 
                                                             start_date=current_date, 
                                                             start_time=start_time, price=price, 
                                                             zoom_link=zoom_link, 
                                                             time=duration)


            return redirect('courses_online')
    else:
        form = forms.OnlineClassesFutureForm()

    context = {
        'form': form,
        'type': 'online'
    }
    return render(request, 'adminpanel/create_future_course.html', context)


@login_required
@staff_member_required
def courses_offline_view(request):
    current_date = timezone.now().date()
    current_time = timezone.now().time()

    current_classes_list = models.OfflineClassesModel.objects.filter(start_date=current_date, start_time__gte=current_time).order_by('pk')
    upcoming_classes_list = models.OfflineClassesModel.objects.filter(start_date__gt=current_date).order_by('pk')
    previous_classes_list = models.OfflineClassesModel.objects.filter(start_date__lte=current_date).order_by('pk')

    paginator_current = Paginator(current_classes_list, 5)
    paginator_upcoming = Paginator(upcoming_classes_list, 5)
    paginator_previous = Paginator(previous_classes_list, 5)

    page_number_current = request.GET.get('page_current') or 1
    page_number_upcoming = request.GET.get('page_upcoming') or 1
    page_number_previous = request.GET.get('page_previous') or 1

    current_classes = paginator_current.get_page(page_number_current)
    upcoming_classes = paginator_upcoming.get_page(page_number_upcoming)
    previous_classes = paginator_previous.get_page(page_number_previous)

    context = {
        'current_classes': current_classes,
        'upcoming_classes': upcoming_classes,
        'previous_classes': previous_classes,
        'type': 'offline'
    }

    return render(request, 'adminpanel/courses.html', context)

@login_required
@staff_member_required
def course_offline_details_view(request, classid):
    current_class = models.OfflineClassesModel.objects.get(pk=classid)
    registrations = models.OfflineClassRegistrationModel.objects.filter(class_id=current_class)
    context = {
        'class': current_class,
        'registrations': registrations,
        'type': 'offline'
    }
    return render(request, 'adminpanel/course_details.html', context)

@login_required
@staff_member_required
def course_offline_delete(request, classid):
    try:
        class_item = models.OfflineClassesModel.objects.get(pk=classid)
        for user in models.OfflineClassRegistrationModel.objects.filter(class_id=models.OfflineClassesModel.objects.get(pk=classid)):
            send_mail(
                'Відміна онлайн заняття на сайті OXYOGA',
                f'Перепрошую за незручності, {user.user_name}. \nОнлайн заняття {class_item.class_name}, заплановане на {class_item.start_date} о {class_item.start_time} було відмінене. \nЗв\'яжіться зі мною.\nTelegram: t.me/oksymec \nЗ повагою, Анна Оксимець.',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
        class_item.delete()
        messages.success(request, 'Видалено успішно!')
    except models.OfflineClassesModel.DoesNotExist:
        messages.error(request, 'Клас не знайдено.')

    return redirect(reverse('courses_offline'))

@login_required
@staff_member_required
def course_offline_edit(request, classid):
    form = ''
    old_date = models.OfflineClassesModel.objects.get(pk=classid).start_date
    old_time = models.OfflineClassesModel.objects.get(pk=classid).start_time
    class_item = get_object_or_404(models.OfflineClassesModel, pk=classid)
    if request.method == "POST":
        form = forms.OfflineClassForm(request.POST, instance=class_item)
        new_date = form.data['start_date']
        new_time = form.data['start_time']
        if form.is_valid():
            if old_date != new_date or old_time != new_time:
                for user in models.OfflineClassRegistrationModel.objects.filter(class_id=models.OfflineClassesModel.objects.get(pk=classid)):
                    send_mail(
                        'Зміни в офлайн занятті',
                        f'Перепрошую за незручності, {user.user_name}. Офлайн заняття {class_item.class_name} було змінене.\nНова дата та час зустрічі: {form.cleaned_data["start_date"]} {form.cleaned_data["start_time"]}. \nДля уточнення інформації зв\'яжіться зі мною.\nTelegram: <a href="t.me/oksymec"@oksymec> \nЗ повагою, Анна Оксимець.',
                        'from@example.com',
                        [user.email],
                        fail_silently=False
                    )
            form.save()
            return redirect('courses_offline')
    else:
        form = forms.OfflineClassForm(instance=class_item)
    context = {
        'form': form,
        'type': 'offline'
    }
    return render(request, 'adminpanel/edit_course.html', context)

@login_required
@staff_member_required
def course_offline_create(request):
    if request.method == 'POST':
            class_name = request.POST['class_name']
            description = request.POST['description']
            start_date = request.POST['start_date']
            start_time = request.POST['start_time']
            price = request.POST['price']
            location = request.POST['location']
            max_participants = request.POST['max_participants']

            start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
            end_datetime = start_datetime + timedelta(minutes=60)

            creds = google_login(request)
            if isinstance(creds, HttpResponseRedirect):
                return creds
            service = build('calendar', 'v3', credentials=creds)

            event = {
                'summary': 'OFFLINE ' + class_name,
                'description': 'offline class',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Kiev',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Kiev',
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()

            models.OfflineClassesModel.objects.create(class_name=class_name, description=description, 
                                                      start_date=start_date, start_time=start_time, price=price, 
                                                      location=location, max_participants=max_participants)
            messages.success(request, 'Заняття створено успішно!')
            return redirect('courses_offline')
    else:
        form = forms.OfflineClassForm()
    context = {
        'form': form,
        'type': 'offline'
    }
    return render(request, 'adminpanel/create_course.html', context)

def zoom_oauth_callback(request):
    code = request.GET.get('code')
    
    if not code:
        return JsonResponse({'status': False, 'errorCode': 'missing_code', 'errorMessage': 'Authorization code is missing'})
    
    client_id = settings.ZOOM_CLIENT_ID
    client_secret = settings.ZOOM_CLIENT_SECRET
    
    credentials = f'{client_id}:{client_secret}'
    base64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://oksyoga.com/configuration/courses_online/new/callback',
    }
    headers = {
        'Authorization': f'Basic {base64_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post('https://zoom.us/oauth/token', data=payload, headers=headers)
    response_data = response.json()
    
    if response.status_code != 200:
        error_message = response_data.get('error_description', 'Unknown error occurred')
        return JsonResponse({'status': False, 'errorCode': response_data.get('error'), 'errorMessage': error_message})
    
    access_token = response_data.get('access_token')
    refresh_token = response_data.get('refresh_token')
    expires_in = response_data.get('expires_in')


    token_expires = timezone.now() + timezone.timedelta(seconds=expires_in)
    token_expires_str = token_expires.isoformat()
    
    zoom_model = models.ZoomToken.objects.get(pk=1)
    zoom_model.access_token = access_token
    zoom_model.refresh_token = refresh_token
    zoom_model.token_expires_str = token_expires_str
    zoom_model.save()
    
    return redirect('courses_online')

def refresh_zoom_token(request):
    zoom_model = models.ZoomToken.objects.get(pk=1)
    refresh_token = zoom_model.refresh_token
    
    if not refresh_token:
        return JsonResponse({'status': False, 'errorCode': 'missing_refresh_token', 'errorMessage': 'Refresh token is missing'})
    
    client_id = settings.ZOOM_CLIENT_ID
    client_secret = settings.ZOOM_CLIENT_SECRET
    
    credentials = f'{client_id}:{client_secret}'
    base64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    headers = {
        'Authorization': f'Basic {base64_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post('https://zoom.us/oauth/token', data=payload, headers=headers)
    response_data = response.json()
    
    if response.status_code != 200:
        error_message = response_data.get('error_description', 'Unknown error occurred')
        return JsonResponse({'status': False, 'errorCode': response_data.get('error'), 'errorMessage': error_message})
    
    access_token = response_data.get('access_token')
    new_refresh_token = response_data.get('refresh_token')
    expires_in = response_data.get('expires_in')
    
    token_expires = timezone.now() + timezone.timedelta(seconds=expires_in)
    token_expires_str = token_expires.isoformat()
    
    zoom_model.access_token = access_token
    zoom_model.refresh_token = new_refresh_token
    zoom_model.token_expires_str = token_expires_str
    zoom_model.save()
    
    return {'access_token': access_token}

def get_valid_zoom_token(request):
    zoom_model = models.ZoomToken.objects.get(pk=1)
    access_token = zoom_model.access_token
    token_expires_str = zoom_model.token_expires_str
    
    if not access_token or not token_expires_str:
        return None, {'status': False, 'errorCode': 'missing_token', 'errorMessage': 'Zoom access token is missing'}
    
    token_expires = timezone.datetime.fromisoformat(str(token_expires_str))
    
    if timezone.now() >= token_expires:
        token_response = refresh_zoom_token(request)
        if token_response.get('status') == False:
            return None, token_response
        access_token = token_response['access_token']
    
    return access_token, None

@login_required
def create_zoom_meeting(request, name, description, date, duration):
    access_token, error_response = get_valid_zoom_token(request)
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    if error_response:
        return error_response
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "topic": name,
        "type": 2,
        "start_time": date,
        "duration": duration,
        "timezone": "Europe/Kiev",
        "agenda": description,
        "password": password,
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": False,
            "mute_upon_entry": True,
            "waiting_room": False,
            "watermark": False,
            "use_pmi": False,
            "approval_type": 2,
            "registration_type": 1,
            "audio": "voip",
            "auto_recording": "cloud",
            "enforce_login": False
        }
    }

    response = requests.post('https://api.zoom.us/v2/users/me/meetings', json=payload, headers=headers)
    meeting_data = response.json()
    
    if response.status_code != 201:
        error_message = meeting_data.get('message', 'Unknown error occurred')
        return JsonResponse({'status': False, 'errorCode': meeting_data.get('code'), 'errorMessage': error_message})
    
    return meeting_data

@login_required
@staff_member_required
def video_view(request):
    form = forms.CategoryFilterForm(request.GET or None)
    video_name = request.GET.get('search_video')
    video_objects = models.VideoModel.objects.all()
    tag_model = models.VideoTagModel.objects.all()
    
    if video_name:
        list_video = video_objects.order_by("pk").reverse().filter(name__contains=video_name)
    elif form.is_valid() and form.cleaned_data['category']:
        list_video = video_objects.filter(tag=form.cleaned_data['category'])
    else:
        list_video = video_objects.order_by("pk").reverse()
    
    paginator = Paginator(list_video, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'videos': page_obj,
        'form': form,
    }
    if request.GET.get('category'):
        context['category'] = tag_model.get(tag_name=form.cleaned_data['category']).id
    return render(request, 'adminpanel/video.html', context)
def transform_youtube_url(url):
    # Extract the video ID from the given URL
    match = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/|.+\?v=))([^&?]+)', url)
    if match:
        video_id = match.group(1)
        # Construct the new URL
        return f'https://www.youtube.com/watch?v={video_id}'
    return url
@login_required
@staff_member_required
def new_video_view(request):
    if request.method == "POST":
        form = forms.VideoForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            # Transform the video link
            video.link = transform_youtube_url(video.link)
            subscribers = models.GlobalUserModel.objects.filter(subscription_end_date__gte=timezone.now().date())
            emails = [subscriber.user.email for subscriber in subscribers]
            if emails:
                for subscriber in subscribers:
                    send_mail(
                        'Нове відео на сайті OXYOGA',
                        f'Намасте, {subscriber.user.first_name}! На сайті з\'явилося нове відео. Переглянути його можна за посиланням: https://oksyoga.com/dashboard/videos',
                        'from@example.com',
                        [subscriber.user.email],
                        fail_silently=False,
                    )
            video.save()

            tags = form.cleaned_data['tag']
            video.tag.set(tags)

            messages.success(request, 'Відео створено успішно!')
            return redirect(reverse('video_index'))
    else:
        form = forms.VideoForm

    context = {
        'form': form
    }

    return render(request, 'adminpanel/new_video.html', context)
@login_required
@staff_member_required
def video_tags_view(request):
    tags = models.VideoTagModel.objects.all()

    for tag in tags:
        tag.video_count = models.VideoModel.objects.filter(tag=tag).count()
    
    context = {
        'tags': tags
    }

    return render(request, 'adminpanel/video_tags.html', context)

@login_required
@staff_member_required
def video_details_view(request, videoid):
    video = get_object_or_404(models.VideoModel, pk=videoid)
    comments = models.VideoCommentModel.objects.filter(video=video)
    tags = []
    for object in video.tag.all():
        tags.append(object.__str__())

    context = {
        'video': video,
        'comments': comments,
        'tags': tags
    }

    return render(request, 'adminpanel/video_details.html', context)

@login_required
@staff_member_required
def video_details_edit_view(request, videoid):
    form = ''
    video_item = get_object_or_404(models.VideoModel, pk=videoid)
    if request.method == "POST":
        form = forms.VideoForm(request.POST, instance=video_item)
        if form.is_valid():
            form.save()
            return redirect('video_index')
    else:
        form = forms.VideoForm(instance=video_item)
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/video_edit.html', context)

@login_required
@staff_member_required
def video_delete_view(request, videoid):
    try:
        video_item = models.VideoModel.objects.get(pk=videoid)
        video_item.delete()
        messages.success(request, 'Видалено успішно!')
    except models.VideoModel.DoesNotExist:
        messages.error(request, 'Відео не знайдено.')

    return redirect(reverse('video_index'))

@login_required
@staff_member_required
def video_tag_delete_view(request, tagid):
    try:
        tag_item = models.VideoTagModel.objects.get(pk=tagid)
        for video in models.VideoModel.objects.all():
            video.tag.remove(tag_item)
        tag_item.delete()
        messages.success(request, 'Видалено успішно!')
    except models.VideoTagModel.DoesNotExist:
        messages.error(request, 'Відео не знайдено.')

    return redirect(reverse('video_tags'))

@login_required
@staff_member_required
def new_tag_view(request):
    if request.method == "POST":
        form = forms.VideoTagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('video_tags'))
    else:
        form = forms.VideoTagForm()
    
    context = {
        'form': form
    }
    return render(request, 'adminpanel/new_tag.html', context)

@login_required
@staff_member_required
def settings_view(request):
    is_online_sale = False
    is_offline_sale = False
    is_opened_doors = False

    online_sale_object = models.OnlineClassSale.objects.get(pk=1)
    offline_sale_object = models.OfflineClassSale.objects.get(pk=1)
    opened_doors_object = models.DayOfOpenedDoors.objects.get(pk=1)

    if online_sale_object.due_to >= timezone.datetime.now().date() and online_sale_object.is_enabled == True:
        is_online_sale = True
    if offline_sale_object.due_to >= timezone.datetime.now().date() and offline_sale_object.is_enabled == True:
        is_offline_sale = True
    if opened_doors_object.due_to >= timezone.datetime.now().date() and opened_doors_object.is_enabled == True:
        is_opened_doors = True

    context = {
        'is_online_sale': is_online_sale,
        'is_offline_sale': is_offline_sale,
        'is_opened_doors': is_opened_doors,
        'online_sale_object': online_sale_object,
        'offline_sale_object': offline_sale_object,
        'opened_doors_object': opened_doors_object
    }
    return render(request, 'adminpanel/settings.html', context)

@login_required
@staff_member_required
def retreat_index_view(request):
    selected_object = get_object_or_404(models.RetreatDescription, pk=1)
    if request.method == 'POST':
        form = forms.RetreatBoolForm(request.POST, instance=selected_object)
        if form.is_valid():
            form.save()
            return redirect('retreat_index')
    else:
        form = forms.RetreatBoolForm(instance=selected_object)
    context = {
        'images': models.Image.objects.all(),
        'description': selected_object.description,
        'registered_users': models.RetreatRegistration.objects.all(),
        'form': form
    }
    return render(request, 'adminpanel/retreat_index.html', context)

@login_required
@staff_member_required
def retreat_edit_description_view(request):
    retreat_description = get_object_or_404(models.RetreatDescription, pk=1)
    if request.method == 'POST':
        form = forms.RetreatDescriptionEditForm(request.POST, instance=retreat_description)
        form.save()
        return redirect('retreat_index')
    else:
        form = forms.RetreatDescriptionEditForm(instance=retreat_description)

    context = {
        'form': form
    }
    return render(request, 'adminpanel/retreat_edit_description.html', context)

@login_required
@staff_member_required
def upload_image_view(request):
    if request.method == 'POST':
        form = forms.ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            image = request.FILES['image']

            headers = {'Authorization': f'Client-ID {settings.IMGUR_CLIENT_ID}'}
            files = {'image': image.read()}
            response = requests.post('https://api.imgur.com/3/image', headers=headers, files=files)
            response_data = response.json()

            if response.status_code == 200:
                imgur_link = response_data['data']['link']
                models.Image.objects.create(title=title, imgur_link=imgur_link)
                return redirect('retreat_index')
            else:
                messages.error(request, f'Помилка! {response.status_code}\n{response_data}')
                return redirect('retreat_index')
    else:
        form = forms.ImageUploadForm()

    context = {
        'form': form
    }
    return render(request, 'adminpanel/image_upload.html', context)

@login_required
@staff_member_required
def online_sale_view(request):
    sale_object = get_object_or_404(models.OnlineClassSale, pk=1)
    if request.method == "POST":
        form = forms.OnlineClassSaleForm(request.POST, instance=sale_object)
        form.save()
        return redirect('settings')
    else:
        form = forms.OnlineClassSaleForm(instance=sale_object)
    
    context = {
        'form': form,
        'type': 'online'
    }
    return render(request, 'adminpanel/sale_form.html', context)

@login_required
@staff_member_required
def offline_sale_view(request):
    sale_object = get_object_or_404(models.OfflineClassSale, pk=1)
    if request.method == "POST":
        form = forms.OfflineClassSaleForm(request.POST, instance=sale_object)
        form.save()
        return redirect('settings')
    else:
        form = forms.OfflineClassSaleForm(instance=sale_object)
    
    context = {
        'form': form,
        'type': 'offline'
    }
    return render(request, 'adminpanel/sale_form.html', context)

@login_required
@staff_member_required
def delete_image_view(request, imageid):
    image = get_object_or_404(models.Image, pk=imageid)
    image.delete()

    return redirect('retreat_index')

@login_required
@staff_member_required
def retreat_delete_registrations(request):
    models.RetreatRegistration.objects.all().delete()

    return redirect('retreat_index')

@login_required
@staff_member_required
def edit_subscription_view(request):
    subscriptions = models.SubscriptionTypeModel.objects.all()
    selected_subscription = None
    form = None

    if request.method == 'POST':
        selected_subscription_id = int(request.POST.get('subscription_id'))
        selected_subscription = get_object_or_404(models.SubscriptionTypeModel, id=selected_subscription_id)
        form = forms.SubscriptionTypeForm(request.POST, instance=selected_subscription)
        if form.is_valid():
            form.save()
            return redirect('edit_subscription')
    else:
        selected_subscription_id = request.GET.get('subscription_id')
        if selected_subscription_id:
            selected_subscription = get_object_or_404(models.SubscriptionTypeModel, id=int(selected_subscription_id))
        else:
            selected_subscription = subscriptions[1] if len(subscriptions) > 1 else subscriptions.first()
        
        if selected_subscription:
            form = forms.SubscriptionTypeForm(instance=selected_subscription)

    context = {
        'id': selected_subscription.id if selected_subscription else None,
        'subscriptions': subscriptions,
        'form': form,
    }
    return render(request, 'adminpanel/edit_subscription.html', context)

@login_required
@staff_member_required
def edit_access_day_view(request):
    edit_object = get_object_or_404(models.DayOfOpenedDoors, pk=1)
    if request.method == "POST":
        form = forms.DayOfOpenedDoorsForm(request.POST, instance=edit_object)
        form.save()
        return redirect('settings')
    else:
        form = forms.DayOfOpenedDoorsForm(instance=edit_object)
    
    context = {
        'form': form,
        'type': 'offline'
    }
    return render(request, 'adminpanel/edit_access_day.html', context)