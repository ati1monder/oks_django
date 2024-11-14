from rest_framework import viewsets
from adminpanel import models
from . import serializers
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.http.response import Http404
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import generics
from django.db.models import Q
from django.conf import settings
import datetime
import requests
from pytz import timezone as pytz_timezone
from adminpanel import models

# Create your views here.

# views.py


class OnlineClassesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.OnlineClassesSerializer
    queryset = models.OnlineClassesModel.objects.all()
    def get_queryset(self):
        current_date = timezone.now().date()
        current_time = timezone.now().time()
        user_timezone = self.request.query_params.get('timezone', 'UTC')
        user_tz = pytz_timezone(user_timezone)

        queryset = models.OnlineClassesModel.objects.filter(
            Q(start_date__gt=current_date) |
            Q(start_date=current_date, start_time__gte=current_time)
        )

        for obj in queryset:
            start_datetime = timezone.datetime.combine(obj.start_date, obj.start_time)
            start_datetime = start_datetime.astimezone(user_tz)
            obj.start_date = start_datetime.date()
            obj.start_time = start_datetime.time()

        return queryset

class OfflineClassesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.OfflineClassesSerializer

    def get_queryset(self):
        current_date = timezone.now().date()
        current_time = timezone.now().time()
        return models.OfflineClassesModel.objects.filter(
            Q(start_date__gt=current_date) |
            Q(start_date=current_date, start_time__gte=current_time)
        )

    queryset = models.OfflineClassesModel.objects.all()


class GetUsernameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        phone_number = get_object_or_404(models.UserPhoneNumber, user=user).phone_number_field
        if user.is_authenticated:
            try:
                subscription = get_object_or_404(models.GlobalUserModel, user=User.objects.get(pk=user.id))
                subscription_object = {
                    'start_date': subscription.subscription_start_date, 
                    'end_date': subscription.subscription_end_date
                    }
            except Http404:
                subscription_object = 'No subscription'

            return Response({
                'user_id': user.id,
                'user_full_name': user.first_name + ' ' + user.last_name,
                'username': user.username,
                'email': user.email,
                'phone_number': phone_number,
                'subscription': subscription_object
                }, status=status.HTTP_200_OK)
        return Response({"detail": "User not found", "code": "user_not_found"}, status=status.HTTP_404_NOT_FOUND)
    
class is_subscribed(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            try:
                subscription = get_object_or_404(models.GlobalUserModel, user=User.objects.get(pk=user.id))
                opened_doors_check = get_object_or_404(models.DayOfOpenedDoors, pk=1)
                if subscription.subscription_end_date >= timezone.now().date():
                    return Response({"detail": True, "code": 'user_is_subscribed'}, status=status.HTTP_200_OK)
                elif opened_doors_check.due_to >= timezone.datetime.now().date() and opened_doors_check.is_enabled == True:
                    return Response({"detail": True, "code": 'day_of_opened_doors_is_enabled'}, status=status.HTTP_200_OK)
                else:
                    return Response({"detail": False, "code": 'subscription_is_expired'}, status=status.HTTP_404_NOT_FOUND)
            except Http404:
                return Response({"detail": False, "code": 'no_subscription_in_db'}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "User not found", "code": "user_not_found"}, status=status.HTTP_404_NOT_FOUND)

class ChangeUsernameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = serializers.ChangeUsernameSerializer(data=request.data)
        if serializer.is_valid():
            new_username = serializer.validated_data['new_username']
            user = request.user
            if User.objects.filter(username=new_username).exists():
                return Response({"error": "This username is already taken."}, status=status.HTTP_400_BAD_REQUEST)
            user.username = new_username
            user.save()
            return Response({"message": "Username updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            user = request.user
            if not user.check_password(old_password):
                return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DeleteAccountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response({"detail": "Account deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
class UpdateEmailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        new_email = request.data.get('email')
        user = request.user
        
        if not new_email:
            return Response({"error": "Email address is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_email(new_email)  # Validate email format
        except ValidationError:
            return Response({"error": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.email = new_email
        user.save()
        
        return Response({"detail": "Email address updated successfully."}, status=status.HTTP_200_OK)
    
class SubscriptionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.SubscriptionTypeModel.objects.all()
    serializer_class = serializers.SubscriptionTypeSerializer
class VideoDetails(APIView):

    def check_opened_doors(self):
        check_object = models.DayOfOpenedDoors.objects.get(pk=1)
        if check_object.due_to >= timezone.datetime.now().date() and check_object.is_enabled == True:
            return True
        else:
            return False
    
    def get(self, request, video_id):
        user = request.user
        if user.is_authenticated:
            if self.check_opened_doors():
                videos = models.VideoModel.objects.get(pk=video_id)
                serializer = serializers.VideoSerializer(videos, many=False)
                return Response(serializer.data)
            else:
                try:
                    subscription = get_object_or_404(models.GlobalUserModel, user=User.objects.get(pk=user.id))
                    if subscription.subscription_end_date >= timezone.now().date():
                        videos = models.VideoModel.objects.get(pk=video_id)
                        serializer = serializers.VideoSerializer(videos, many=False)
                        return Response(serializer.data)
                    else:
                        videos = models.VideoDemoModel.objects.get(video=models.VideoModel.objects.get(pk=video_id))
                        serializer = serializers.VideoDemoSerializer(videos, many=False)
                        return Response(serializer.data)
                except Http404:
                    videos = models.VideoDemoModel.objects.get(video=models.VideoModel.objects.get(pk=video_id))
                    serializer = serializers.VideoDemoSerializer(videos, many=False)
                    return Response(serializer.data)
        else:
            videos = models.VideoDemoModel.objects.get(video=models.VideoModel.objects.get(pk=video_id))
            serializer = serializers.VideoDemoSerializer(videos, many=False)
            return Response(serializer.data)

class VideoListView(APIView):
    def check_opened_doors(self):
        check_object = models.DayOfOpenedDoors.objects.get(pk=1)
        if check_object.due_to >= timezone.datetime.now().date() and check_object.is_enabled:
            return True
        return False

    def get(self, request):
        filter_list = request.GET.getlist('tag')  # Get the tag list if provided
        user = request.user

        if user.is_authenticated:
            if self.check_opened_doors():
                videos = models.VideoModel.objects.filter(tag__in=filter_list) if filter_list else models.VideoModel.objects.all()
            else:
                try:
                    subscription = get_object_or_404(models.GlobalUserModel, user=User.objects.get(pk=user.id))
                    if subscription.subscription_end_date >= timezone.now().date():
                        videos = models.VideoModel.objects.filter(tag__in=filter_list) if filter_list else models.VideoModel.objects.all()
                    else:
                        videos = models.VideoDemoModel.objects.filter(video__tag__in=filter_list) if filter_list else models.VideoDemoModel.objects.all()
                except Http404:
                    videos = models.VideoDemoModel.objects.filter(video__tag__in=filter_list) if filter_list else models.VideoDemoModel.objects.all()
        else:
            if self.check_opened_doors():
                videos = models.VideoModel.objects.filter(tag__in=filter_list) if filter_list else models.VideoModel.objects.all()
                serializer = serializers.VideoSerializer(videos, many=True)
            else:
                videos = models.VideoDemoModel.objects.filter(video__tag__in=filter_list) if filter_list else models.VideoDemoModel.objects.all()
                serializer = serializers.VideoDemoSerializer(videos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if isinstance(videos.first(), models.VideoModel):
            serializer = serializers.VideoSerializer(videos, many=True)
        else:
            serializer = serializers.VideoDemoSerializer(videos, many=True)

        return Response(serializer.data)


class VideoTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.VideoTagModel.objects.all()
    serializer_class = serializers.VideoTagSerializer

class TagDetails(APIView):
    def get(self, request, tag_id):
        obj = get_object_or_404(models.VideoTagModel, id=tag_id)

        serializer = serializers.VideoTagSerializer(obj, many=False)
        return Response(serializer.data)

class TagView(APIView):
    def get(self, request):
        tag_list = models.VideoTagModel.objects.all()

        serializer = serializers.VideoTagSerializer(tag_list, many=True)
        return Response(serializer.data)

class VideoCommentListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, video_id):
        get_object_or_404(models.VideoModel, id=video_id)
        comments = models.VideoCommentModel.objects.filter(video=video_id)
        serializer = serializers.VideoCommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, video_id):
        get_object_or_404(models.VideoModel, id=video_id)
        data = request.data.copy()
        data['video'] = video_id
        serializer = serializers.VideoCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=models.GlobalUserModel.objects.get(user=request.user))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckWhichClassesUserIsRegistered(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        email = user.email
        current_date = timezone.now().date()
        user_timezone = request.query_params.get('timezone', 'UTC')
        user_tz = pytz_timezone(user_timezone)

        online_registrations = models.OnlineClassRegistrationModel.objects.filter(email=email)
        offline_registrations = models.OfflineClassRegistrationModel.objects.filter(email=email)

        online_serializer = serializers.OnlineClassRegistrationSerializer(online_registrations, many=True)
        offline_serializer = serializers.OfflineClassRegistrationSerializer(offline_registrations, many=True)

        offline_class_ids = [reg['class_id'] for reg in offline_serializer.data]
        online_class_ids = [reg['class_id'] for reg in online_serializer.data]

        online_classes = models.OnlineClassesModel.objects.filter(id__in=online_class_ids, start_date__gte=current_date)
        offline_classes = models.OfflineClassesModel.objects.filter(id__in=offline_class_ids, start_date__gte=current_date)

        for obj in online_classes:
            start_datetime = timezone.datetime.combine(obj.start_date, obj.start_time)
            start_datetime = start_datetime.astimezone(user_tz)
            obj.start_date = start_datetime.date()
            obj.start_time = start_datetime.time()

        # Removed timezone logic for offline classes

        online_classes_serializer = serializers.CustomOnlineClassesSerializer(online_classes, many=True)
        offline_classes_serializer = serializers.OfflineClassesSerializer(offline_classes, many=True)

        return Response({
            'offline_classes': offline_classes_serializer.data,
            'online_classes': online_classes_serializer.data
        })


class RecaptchaHandling(APIView):
    def post(self, request):
        try:
            url = 'https://www.google.com/recaptcha/api/siteverify'
            token = request.data.get('response')

            post_parameters = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': token
            }

            response = requests.post(url, data=post_parameters)

            if response.json()['success'] == True:
                return Response({'response': True}, status=status.HTTP_200_OK)
            else:
                return Response({'response': False, 'details': response.json()}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def retreat_registration_create(request):
    if request.method == 'POST':
        serializer = serializers.RetreatRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def combined_data_view(request):
    images = models.Image.objects.all()
    retreat_description = models.RetreatDescription.objects.get(pk=1)

    image_serializer = serializers.ImageSerializer(images, many=True)
    retreat_description_serializer = serializers.RetreatDescriptionSerializer(retreat_description)

    combined_data = {
        'images': image_serializer.data,
        'retreat_description': retreat_description_serializer.data
    }

    serializer = serializers.CombinedDataSerializer(data=combined_data)
    serializer.is_valid()

    return Response(serializer.data)


class DayOfOpenedDoors(APIView):
    def get(self, request):
        check_object = get_object_or_404(models.DayOfOpenedDoors, pk=1)
        serializer = serializers.DayOfOpenedDoorsSerializer(check_object)

        return Response(serializer.data)