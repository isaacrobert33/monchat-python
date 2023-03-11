from django.contrib import admin
from .views import MonchatMsg, MonchatUser, ProfileUpload


# Register your models here.
@admin.register(MonchatUser)
class MonchatUserAdmin(admin.ModelAdmin):
    list_display = [
        "user_name",
        "first_name",
        "last_name",
        "user_icon",
        "online_status",
        "last_seen",
        "user_bio",
    ]
    list_filter = ["user_name", "first_name", "online_status", "last_seen"]
    search_fields = ["user_name", "first_name", "last_name", "last_seen"]
    prepopulated_fields = {"user_name": ("first_name",)}
    date_hierarchy = "last_seen"
    ordering = ["online_status", "last_seen"]


@admin.register(MonchatMsg)
class MonchatMsgAdmin(admin.ModelAdmin):
    list_display = ["msg_sender", "msg_recipient", "msg_body", "msg_status"]
    list_filter = ["msg_sender", "msg_recipient", "msg_time", "msg_status", "read_time"]
    search_fields = ["msg_sender", "msg_body", "msg_recipient"]
    raw_id_fields = ["msg_sender", "msg_recipient"]
    date_hierarchy = "msg_time"
    ordering = ["msg_time", "read_time"]


admin.site.register(ProfileUpload)
