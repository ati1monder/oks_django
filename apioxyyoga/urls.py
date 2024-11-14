from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'online-classes', views.OnlineClassesViewSet)
router.register(r'offline-classes', views.OfflineClassesViewSet)
router.register(r'subscriptions', views.SubscriptionTypeViewSet, basename='subscription')
router.register(r'videos/tags', views.VideoTagsViewSet, basename='video-tags')

urlpatterns = [
    path('', include(router.urls)),
    path('user_info/', views.GetUsernameView.as_view(), name='user_info'),
    path('is_subscribed/', views.is_subscribed.as_view(), name='is_subscribed'),
    path('change-username/', views.ChangeUsernameView.as_view(), name='change_username'),
    path('update-email/', views.UpdateEmailView.as_view(), name='update-email'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete-account'),
    path('videos/', views.VideoListView.as_view(), name='video-list'),
    path('videos/<int:video_id>/', views.VideoDetails.as_view(), name='video-details'),
    path('videos/<int:video_id>/comments/', views.VideoCommentListView.as_view(), name='video-comments'),
    path('videos/tag/', views.TagView.as_view(), name='list_tags'),
    path('videos/tag/<int:tag_id>/', views.TagDetails.as_view(), name='tag_details'),
    path('retreat-registration/', views.retreat_registration_create, name='retreat-registration-create'),
    path('retreat-data/', views.combined_data_view, name='combined-data'),
    path('day_of_opened_doors/', views.DayOfOpenedDoors.as_view(), name='day_of_opened_doors'),
    path("CheckPaidSubscription/", views.CheckWhichClassesUserIsRegistered.as_view(), name="CheckPayedSubscription"),
    path('recaptcha_handling/', views.RecaptchaHandling.as_view(), name='recaptcha_handling'),
]