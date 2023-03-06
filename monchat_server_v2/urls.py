from django.urls import path
from .views import Sigin, Signup, LatestChats, Chats, ChatStatus

app_name = 'monchat_server_v2'

urlpatterns = [
    path('login/', Sigin.as_view(), name="login"),
    path('sign_up/', Signup.as_view(), name="sign_up"),
    path('latest_chats/<slug:user_id>/', LatestChats.as_view(), name="latest_chats"),
    path('chats/<slug:user_id>/<slug:recipient>/', Chats.as_view(), name="chats"),
    path('chat_status/<slug:chat_id>/<str:status>/', ChatStatus.as_view(), name="chat_status"),
]
