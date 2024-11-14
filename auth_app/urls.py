from django.urls import path
from .views import CustomTokenObtainPairView, CustomTokenRefreshView, register, login_view

urlpatterns = [
    path('register', register, name='register'),
    path('login', login_view, name='login'),
    path('token_user', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token_refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
]