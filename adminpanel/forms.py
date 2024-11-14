from django import forms
from django_select2.forms import Select2MultipleWidget
from django.contrib.auth.models import User
from django.utils import timezone

from . import models

class CustomDateInput(forms.DateInput):
    input_type = 'date'

    def format_value(self, value):
        if isinstance(value, str):
            value = forms.DateField().to_python(value)
        return value.strftime('%Y-%m-%d') if value else ''

class CustomTimeInput(forms.TimeInput):
    input_type = 'time'

    def format_value(self, value):
        if isinstance(value, str):
            value = forms.TimeField().to_python(value)
        return value.strftime('%H:%M') if value else ''

class OfflineClassForm(forms.ModelForm):
    class Meta:
        model = models.OfflineClassesModel
        fields = [
            'class_name', 
            'description', 
            'start_date',
            'start_time',
            'price', 
            'location', 
            'max_participants'
        ]
        widgets = {
            'start_date': CustomDateInput(),
            'start_time': CustomTimeInput(),
        }

class OnlineClassForm(forms.ModelForm):
    class Meta:
        model = models.OnlineClassesModel
        fields = [
            'class_name', 
            'description', 
            'start_date',
            'start_time',
            'time',
            'price',
        ]
        widgets = {
            'start_date': CustomDateInput(),
            'start_time': CustomTimeInput(),
        }

DAYS_OF_WEEK = [
    ('0', 'Понеділок'),
    ('1', 'Вівторок'),
    ('2', 'Середа'),
    ('3', 'Четвер'),
    ('4', 'П’ятниця'),
    ('5', 'Субота'),
    ('6', 'Неділя'),
]

class OnlineClassesFutureForm(forms.Form):
    class_name = forms.CharField(label='Назва:', max_length=100, required=True)
    description = forms.CharField(label='Опис:', max_length=500, required=True, widget=forms.Textarea)
    start_time = forms.TimeField(label='Час:', required=True, widget=CustomTimeInput())
    duration = forms.IntegerField(label='Час проведення зустрічі (в хвилинах)', required=True)
    price = forms.IntegerField(label='Ціна:', required=True)
    
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        label='Дні тижня'
    )
    number_of_months = forms.IntegerField(label='Кількість місяців:', required=True)

    class Meta:
        model = models.OnlineClassesModel
        fields = ['class_name', 'description', 'start_time', 'duration', 'price']

class VideoForm(forms.ModelForm):
    tag = forms.ModelMultipleChoiceField(
        queryset=models.VideoTagModel.objects.all(),
        widget=Select2MultipleWidget,
        required=False,
        label="Теги"
    )
    
    demo_link = forms.CharField(
        max_length=200,
        required=False,
        label="Посилання на демо-відео"
    )

    class Meta:
        model = models.VideoModel
        fields = [
            'name',
            'description',
            'link',
            'tag'
        ]

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                demo_video = models.VideoDemoModel.objects.get(video=self.instance)
                self.fields['demo_link'].initial = demo_video.link
            except models.VideoDemoModel.DoesNotExist:
                self.fields['demo_link'].initial = ""

    def save(self, commit=True):
        instance = super(VideoForm, self).save(commit=False)
        demo_link = self.cleaned_data.get('demo_link', '')
        
        # Save or update the demo video link
        if instance.pk:
            video_demo, created = models.VideoDemoModel.objects.get_or_create(video=instance)
            video_demo.link = demo_link
            video_demo.save()
        
        if commit:
            instance.save()
        return instance

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name'
        ]

class GlobalUserForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Назва користувача")
    email = forms.EmailField(label="Пошта")
    first_name = forms.CharField(max_length=30, label="Ім'я")
    last_name = forms.CharField(max_length=30, label="Прізвище")

    subscription_type = forms.ModelChoiceField(queryset=models.SubscriptionTypeModel.objects.all(), required=False, label="Тип підписки")
    subscription_start_date = forms.DateField(label="Початок підписки", widget=CustomDateInput())
    subscription_end_date = forms.DateField(label="Кінець підписки", widget=CustomDateInput())
    money_spent = forms.IntegerField(label="Витрачено грошей")

    class Meta:
        model = models.GlobalUserModel
        fields = [
            'subscription_type',
            'subscription_start_date',
            'subscription_end_date',
            'money_spent'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        user = self.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()

        global_user = super().save(commit=False)
        global_user.user = user
        if commit:
            global_user.save()

        return global_user
    
class NewUserSubscriptionForm(forms.ModelForm):
    class Meta:
        model = models.GlobalUserModel
        fields = [
            'subscription_type',
            'subscription_end_date'
        ]
        widgets = {
            'subscription_end_date': CustomDateInput(),
        }

class CategoryFilterForm(forms.Form):
    category = forms.ModelChoiceField(queryset=models.VideoTagModel.objects.all(), required=False, label='Тег')

class VideoTagForm(forms.ModelForm):
    class Meta:
        model = models.VideoTagModel
        fields = [
            'tag_name'
        ]

class ImageUploadForm(forms.Form):
    title = forms.CharField(max_length=255, label="Назва файлу")
    image = forms.ImageField(label="Зображення")

class RetreatDescriptionEditForm(forms.ModelForm):
    class Meta:
        model = models.RetreatDescription
        fields = [
            'description'
        ]

class OnlineClassSaleForm(forms.ModelForm):
    class Meta:
        model = models.OnlineClassSale
        fields = [
            'is_enabled',
            'coefficient',
            'due_to'
        ]
        widgets = {
            'due_to': CustomDateInput(),
        }

class OfflineClassSaleForm(forms.ModelForm):
    class Meta:
        model = models.OfflineClassSale
        fields = [
            'is_enabled',
            'coefficient',
            'due_to'
        ]
        widgets = {
            'due_to': CustomDateInput(),
        }

class SubscriptionTypeForm(forms.ModelForm):
    class Meta:
        model = models.SubscriptionTypeModel
        fields = '__all__'

class DayOfOpenedDoorsForm(forms.ModelForm):
    class Meta:
        model = models.DayOfOpenedDoors
        fields = ['is_enabled',
                  'due_to'
        ]
        widgets = {
            'due_to': CustomDateInput(),
        }

class RetreatBoolForm(forms.ModelForm):
    class Meta:
        model = models.RetreatDescription
        fields = ['is_enabled']