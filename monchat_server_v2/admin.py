from django.contrib import admin
from .models import MonchatMsg, MonchatUser, ProfileUpload, MonchatGroup


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
    list_filter = [
        "msg_sender",
        "msg_recipient",
        "msg_time",
        "msg_status",
        "read_time",
        "group_id",
    ]
    search_fields = ["msg_sender", "msg_body", "msg_recipient"]
    raw_id_fields = ["msg_sender", "msg_recipient"]
    date_hierarchy = "msg_time"
    ordering = ["msg_time", "read_time"]


@admin.register(MonchatGroup)
class MonchatGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created", "updated", "created_by"]
    list_filter = ["created", "updated", "created_by"]
    search_fields = ["name", "description"]
    date_hierarchy = "created"
    ordering = ["created", "updated"]


admin.site.register(ProfileUpload)
