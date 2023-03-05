from django.urls import path
from .views import User, Chats, ChatStatus

app_name = 'monchat_server'

urlpatterns = [
    path('user/<slug:user_id>/', User.as_view(), name="user"),
    path('chats/<slug:user_id>/<slug:recipient>/', Chats.as_view(), name="chats"),
    path('chat_status/<slug:chat_id>/<str:status>/', ChatStatus.as_view(), name="chat_status"),
]
