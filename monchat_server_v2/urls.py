from django.urls import path
from .views import Sigin, Signup, LatestChats, Chats, ChatStatus, CheckUserName, UserData, Upload

app_name = 'monchat_server_v2'

urlpatterns = [
    path('login/', Sigin.as_view(), name="login"),
    path('sign_up/', Signup.as_view(), name="sign_up"),
    path('user/<slug:user_id>/', UserData.as_view(), name="user_data"),
    path('latest_chats/<slug:user_id>/', LatestChats.as_view(), name="latest_chats"),
    path('chats/<slug:user_name>/<slug:recipient>/', Chats.as_view(), name="chats"),
    path('chat_status/<slug:chat_id>/<str:status>/', ChatStatus.as_view(), name="chat_status"),
    path('check_username/<str:user_name>/', CheckUserName.as_view(), name="check_uname"),
    path('profile_upload/<slug:user_name>/', Upload.as_view(), name="profile_upload"),
]
