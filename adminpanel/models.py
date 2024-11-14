from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

class SubscriptionTypeModel(models.Model):
    name = models.CharField("Назва", max_length=20)
    duration_in_months = models.IntegerField("Тривалість")
    price = models.IntegerField("Ціна")

    def __str__(self):
        return f'Підписка на {self.name} за {self.price} гривень'

class GlobalUserModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_type = models.ForeignKey(SubscriptionTypeModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тип підписки")
    subscription_start_date = models.DateField(verbose_name="Початок підписки", default=timezone.datetime.now)
    subscription_end_date = models.DateField(verbose_name="Кінець підписки")
    money_spent = models.IntegerField(verbose_name="Витрачено грошей")

    def __str__(self):
        return f'Користувач {self.user.username}'

class UserPhoneNumber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number_field = models.IntegerField(verbose_name="Номер телефону", default=0)

class OnlineClassesModel(models.Model):
    class_name = models.CharField('Назва:', max_length=100)
    description = models.TextField('Опис:', max_length=500)
    start_date = models.DateField('Дата:')
    start_time = models.TimeField('Час:')
    price = models.IntegerField('Ціна:')
    time = models.IntegerField('Час проведення зустрічі (в хвилинах)')
    zoom_link = models.CharField('Посилання:', max_length=255, blank=False, default=None)
    reminder_sent = models.BooleanField(default=False)

class OfflineClassesModel(models.Model):
    class_name = models.CharField('Назва:', max_length=100)
    description = models.TextField('Опис:', max_length=500)
    start_date = models.DateField('Дата:')
    start_time = models.TimeField('Час:')
    price = models.IntegerField('Ціна:')
    location = models.CharField('Локація:', max_length=50)
    current_participants = models.IntegerField('Поточна кількість учасників', default=0)
    max_participants = models.IntegerField('Максимальна кількість учасників:')
    registration_date = models.DateTimeField(auto_now_add=True)


class OnlineClassRegistrationModel(models.Model):
    class_id = models.ForeignKey(OnlineClassesModel, on_delete=models.CASCADE)
    user_name = models.CharField("Ім'я", max_length=50)
    user_surname = models.CharField("Прізвище", max_length=50)
    number = models.IntegerField("Номер (без +38)")
    email = models.EmailField("Пошта")
    registration_date = models.DateTimeField(auto_now_add=True)

class OfflineClassRegistrationModel(models.Model):
    class_id = models.ForeignKey(OfflineClassesModel, on_delete=models.CASCADE)
    user_name = models.CharField("Ім'я", max_length=50)
    user_surname = models.CharField("Прізвище", max_length=50)
    number = models.IntegerField("Номер (без +38)")
    email = models.EmailField("Пошта")
    number_of_participants = models.IntegerField("Кількість учасників")

class VideoTagModel(models.Model):
    tag_name = models.CharField("Тег", max_length=30)

    def __str__(self):
        return f'{self.tag_name}'

class VideoModel(models.Model):
    name = models.CharField("Назва відео", max_length=50)
    description = models.TextField("Опис відео", max_length=5000)
    link = models.CharField("Посилання", max_length=200)
    tag = models.ManyToManyField(VideoTagModel, blank=True)

class VideoDemoModel(models.Model):
    video = models.ForeignKey(VideoModel, on_delete=models.DO_NOTHING, related_name="video")
    link = models.CharField("Посилання", max_length=200)

class VideoCommentModel(models.Model):
    video = models.ForeignKey(VideoModel, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(GlobalUserModel, on_delete=models.CASCADE)
    comment = models.CharField("Коментар", max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

class ZoomToken(models.Model):
    access_token = models.CharField(max_length=400)
    refresh_token = models.CharField(max_length=400)
    token_expires_str = models.DateTimeField()

class Image(models.Model):
    title = models.CharField(max_length=255)
    imgur_link = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class RetreatDescription(models.Model):
    is_enabled = models.BooleanField('Увімкнено/Вимкнено')
    description = models.TextField("Опис", max_length=3000)

class RetreatRegistration(models.Model):
    name = models.TextField("Ім'я", max_length=50)
    surname = models.TextField("Прізвище", max_length=50)
    number = models.IntegerField("Номер (без +380)")
    email = models.EmailField("Пошта")

class OnlineClassSale(models.Model):
    is_enabled = models.BooleanField('Статус знижки')
    coefficient = models.FloatField('Коефіцієнт (від 0 до 1)', validators=[MinValueValidator(0.0), MaxValueValidator(1)])
    due_to = models.DateField('Кінець знижки')

class OfflineClassSale(models.Model):
    is_enabled = models.BooleanField('Статус знижки')
    coefficient = models.FloatField('Коефіцієнт (від 0 до 1)', validators=[MinValueValidator(0.0), MaxValueValidator(1)])
    due_to = models.DateField('Кінець знижки')

class DayOfOpenedDoors(models.Model):
    is_enabled = models.BooleanField('Увімкнути/Вимкнути')
    due_to = models.DateField('Кінцеве число')