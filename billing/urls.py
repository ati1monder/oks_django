from django.urls import path, re_path

from . import views

urlpatterns = [
    path('pay/<int:type>/<str:input_id>', views.create_payment, name='pay_view'),
    path('pay-callback/', views.PayCallbackView.as_view(), name='pay_callback')
]