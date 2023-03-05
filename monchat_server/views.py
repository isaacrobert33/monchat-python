from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer, MsgSerializer
from .models import MonchatUser, MonchatMsg
from .utils import generate_id, add_msg_fields
import json

# Create your views here.

class User(APIView):

    def post(self, request, user_id=None):
        print(request.data)
        new_user_id = generate_id(prefix="user")
        p = MonchatUser.objects.create(
            user_name=request.data["user_name"],
            user_id=new_user_id,
            user_icon=request.data["user_icon"]
        )
        return Response({"data": "Signed up sucessfully!"}, status=201)
    
    def get(self, request, user_id):
        user_qset = get_object_or_404(MonchatUser,
                                      user_id=user_id)
        serializer = json.loads(serializers.serialize('json', [user_qset]))
       
        contact_user_ids = set([q.msg_recipient.user_id for q in user_qset.msg_sent.all()] + [q.msg_sender.user_id for q in user_qset.msg_received.all()])
        latest_chat_list = []
        
        for uid in contact_user_ids:
            dt = MonchatMsg.objects.filter(
                            Q(msg_sender__user_id=uid) & Q(msg_recipient__user_id=user_qset.user_id) | Q(msg_recipient__user_id=uid) & Q(msg_sender__user_id=user_qset.user_id)
                        ).latest("msg_time")
            latest_chat_list.append(dt)

        latest_chat_list = [add_msg_fields(q) for q in json.loads(serializers.serialize('json', latest_chat_list))]

        return Response({"user_data": serializer[0]["fields"], "chat_list": latest_chat_list}, status=200)

class Chats(APIView):

    def post(self, request, user_id, recipient):
        new_msg_id = generate_id(prefix='chat')
        msg_sender = get_object_or_404(MonchatUser,
                                      user_id=user_id)
        msg_recipient = get_object_or_404(MonchatUser,
                                      user_id=recipient)
        p = MonchatMsg.objects.create(
            msg_id=new_msg_id,
            msg_body=request.data["msg_body"],
            msg_sender=msg_sender,
            msg_recipient=msg_recipient,
        )

        return Response({"msg": "Saved chat successfully"}, status=201)

    def get(self, request, user_id, recipient):
        
        conversation_list = MonchatMsg.objects.filter(
                            Q(msg_sender__user_id=recipient) & Q(msg_recipient__user_id=user_id) | Q(msg_recipient__user_id=recipient) & Q(msg_sender__user_id=user_id)
                        )
        serializer = [add_msg_fields(q) for q in json.loads(serializers.serialize('json', conversation_list))]

        return Response({"data": serializer}, status=200)


class ChatStatus(APIView):

    def put(self, request, chat_id, status):
        if status == "read":
            new_status = MonchatMsg.MsgStatus.READ
        elif status == "delivered":
            new_status = MonchatMsg.MsgStatus.DELIVERED
        else:
            new_status = MonchatMsg.MsgStatus.UNDELIVERED

        chat = MonchatMsg.objects.get(msg_id=chat_id)
        chat.msg_status = new_status
        chat.save()

        return Response({"msg": "Updated successfully"}, status=200)
    
