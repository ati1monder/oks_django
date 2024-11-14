from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(SubscriptionTypeModel)
admin.site.register(GlobalUserModel)
admin.site.register(OnlineClassesModel)
admin.site.register(OnlineClassRegistrationModel)
admin.site.register(OfflineClassRegistrationModel)
admin.site.register(OfflineClassesModel)
admin.site.register(ZoomToken)
admin.site.register(VideoTagModel)
admin.site.register(VideoModel)
admin.site.register(VideoCommentModel)
admin.site.register(Image)
admin.site.register(RetreatDescription)
admin.site.register(RetreatRegistration)
admin.site.register(OnlineClassSale)
admin.site.register(OfflineClassSale)
admin.site.register(DayOfOpenedDoors)
admin.site.register(UserPhoneNumber)
admin.site.register(VideoDemoModel)