from django.urls import path
from .views import update_repo

urlpatterns = [
    path('update-repo/', update_repo, name='update_repo'),
]