from django.urls import path
from .views import register, email_confirm, password_reset_request, \
    password_reset_confirm  # Import the email_confirm view

urlpatterns = [
    path('register/', register, name='register'),
    path('email-confirm/<uidb64>/<token>/', email_confirm, name='email_confirm'),  # Add this line
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
]