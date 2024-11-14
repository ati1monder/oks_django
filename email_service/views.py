import logging

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
import json
from django.http import JsonResponse
from django.core.mail import send_mail

def register(request):
    if request.method == 'POST':
        # Create user logic here
        user = User.objects.create_user(username=request.POST['username'], email=request.POST['email'], password=request.POST['password'])
        user.is_active = False
        user.save()

        # Generate email confirmation link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link = request.build_absolute_uri(reverse('email_confirm', args=[uid, token]))

        send_mail(
            'Підвердження реєстрації на OXYOGA',
            f'Намасте, цей email було вказано для реєстрації на сайті <a href="OXYOGA">oksyoga.com</a>. Для підвтердження реєстрації натисність на посилання нижче. \nЯкщо ви не вказували цей email для реєстрації, проігноруйте цей лист: <a href="{link}">Підтвердити реєстрацію</a>',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )

        return redirect('login')  # Redirect to login page or wherever you want
    return render(request, 'register.html')  # Render registration template

def email_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'email_service/thank_you.html')

    else:
        return HttpResponse('Invalid confirmation link.')
def password_reset_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON data from request body
            email = data['email']  # Access the email key from JSON data
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                link = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))
                send_mail(
                    'Скидання паролю на OXYOGA',
                    f'З вашого профілю було здійснено запит на скидання паролю на сайті oksyoga.com. Якщо це були ви, натисніть на посилання нижче для того, щоби скинути пароль: \n {link} \nУ іншому випадку, проігноруйте цей лист.',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                return JsonResponse({"message": "Password reset email sent."})
            else:
                return JsonResponse({"error": "Email not found."}, status=404)
        except KeyError:
            return JsonResponse({"error": "Email key not found in request."}, status=400)
    else:
        return render(request, 'email_service/password_reset_form.html')


def password_reset_confirm(request, uidb64, token):
    if request.method == 'GET':
        return render(request, 'email_service/password_reset_confirm.html', {'uid': uidb64, 'token': token})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_password = data.get('password')
            if not new_password:
                logging.error("Missing password in request")
                return JsonResponse({'error': 'Missing password in request'}, status=400)

            uid = urlsafe_base64_decode(uidb64).decode()
            try:
                user = User.objects.get(pk=uid)
            except User.DoesNotExist:
                logging.error(f"User with UID {uid} does not exist.")
                return JsonResponse({'error': 'Invalid UID or token'}, status=400)

            if not default_token_generator.check_token(user, token):
                logging.error(f"Invalid token for user {uid}.")
                return JsonResponse({'error': 'Invalid UID or token'}, status=400)

            user.set_password(new_password)
            user.save()

            return JsonResponse({'success': 'Password has been reset successfully'}, status=200)

        except json.JSONDecodeError:
            logging.error("Invalid JSON")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
