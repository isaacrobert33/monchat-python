from django.urls import path
from .consumers import ChatConsumer, OnlineStatusConsumer, ReadRecieptConsumer

websocket_urlpatterns = [
    path("ws/chat/<slug:tunnel_id>/", ChatConsumer.as_asgi()),
    path("ws/online/", OnlineStatusConsumer.as_asgi()),
    path("ws/read_reciept/<slug:chat_id>/", ReadRecieptConsumer.as_asgi()),
]
