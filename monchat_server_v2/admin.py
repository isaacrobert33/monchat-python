from django.contrib import admin
from .views import MonchatMsg, MonchatUser, ProfileUpload

# Register your models here.
admin.site.register(MonchatUser)
admin.site.register(MonchatMsg)
admin.site.register(ProfileUpload)
