from rest_framework import serializers
from adminpanel import models
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.utils import timezone

class OnlineClassRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OnlineClassRegistrationModel
        fields = ['class_id']

class OfflineClassRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OfflineClassRegistrationModel
        fields = ['class_id']
class CustomOnlineClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OnlineClassesModel
        fields = ['id', 'class_name', 'description', 'start_date', 'start_time', 'price', 'zoom_link', 'time']
class OnlineClassesSerializer(serializers.ModelSerializer):
    old_price = serializers.SerializerMethodField()
    on_sale = serializers.SerializerMethodField()

    class Meta:
        model = models.OnlineClassesModel
        fields = ['id', 'class_name', 'description', 'start_date', 'start_time', 'price', 'old_price', 'on_sale', 'time']

    def get_sale_model(self):
        try:
            return models.OnlineClassSale.objects.get(pk=1)
        except models.OnlineClassSale.DoesNotExist:
            return None

    def get_old_price(self, obj):
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            return obj.price
        return None

    def get_on_sale(self, obj):
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            return True
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            representation['price'] = instance.price * sale_model.coefficient
        return representation

class OfflineClassesSerializer(serializers.ModelSerializer):
    old_price = serializers.SerializerMethodField()
    on_sale = serializers.SerializerMethodField()

    class Meta:
        model = models.OfflineClassesModel
        fields = ['id', 'class_name', 'description', 'start_date', 'start_time', 'price', 'old_price','location', 'current_participants', 'max_participants', 'on_sale']
    
    def get_sale_model(self):
        try:
            return models.OfflineClassSale.objects.get(pk=1)
        except models.OfflineClassSale.DoesNotExist:
            return None

    def get_old_price(self, obj):
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            return obj.price
        return None
    
    def get_on_sale(self, obj):
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            return True
        return False
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        sale_model = self.get_sale_model()
        if sale_model and sale_model.is_enabled and timezone.now().date() <= sale_model.due_to:
            representation['price'] = instance.price * sale_model.coefficient
        return representation

class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(max_length=150)

    def validate_new_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

class SubscriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SubscriptionTypeModel
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VideoModel
        fields = ['id', 'name', 'description', 'link', 'tag']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        description = representation.get('description', '')
        if description:
            description = description.replace('\n\n', '</p><p>')
            description = f"<p>{description}</p>"
            description = description.replace('\n', '<br>')
            representation['description'] = description
        return representation

class VideoDemoSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='video.name')
    description = serializers.CharField(source='video.description')
    tag = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='id',
        source='video.tag'
    )
    link = serializers.CharField()
    id = serializers.IntegerField(source='video.id', read_only=True)

    class Meta:
        model = models.VideoDemoModel
        fields = ['id', 'name', 'description', 'link', 'tag']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Format description
        description = representation.get('description', '')
        if description:
            description = description.replace('\n\n', '</p><p>')
            description = f"<p>{description}</p>"
            description = description.replace('\n', '<br>')
            representation['description'] = description
        return representation

class VideoTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VideoTagModel
        fields = ['id', 'tag_name']

class VideoCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VideoCommentModel
        fields = ['id', 'video', 'comment']

class RetreatRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RetreatRegistration
        fields = ['name', 'surname', 'number', 'email']

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Image
        fields = ['title', 'imgur_link', 'uploaded_at']

class RetreatDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RetreatDescription
        fields = ['is_enabled', 'description']

class CombinedDataSerializer(serializers.Serializer):
    images = ImageSerializer(many=True)
    retreat_description = RetreatDescriptionSerializer()

class DayOfOpenedDoorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DayOfOpenedDoors
        fields = ['is_enabled', 'due_to']