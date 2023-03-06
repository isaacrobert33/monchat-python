from rest_framework import serializers
from .models import MonchatUser, MonchatMsg

class UserSerializer(serializers.Serializer):
    class Meta:
        model = MonchatUser
        fields = ['user_id', 'user_name', 'user_icon']

class MsgSerializer(serializers.Serializer):

    class Meta:
        model = MonchatMsg
        fields = ["msg_body", "msg_time", "msg_status", "msg_recipient", "msg_sender"]
        