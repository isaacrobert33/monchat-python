from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MonchatUser, MonchatMsg
from .utils import (
    generate_id, add_msg_fields, 
    check_password, hash_password,
    cors_response, serialize_user
)
import json, traceback

# Create your views here.

class Sigin(APIView):

    # @cors_response
    def post(self, request):
        uname = request.data["uname"]
        pwd = request.data["pwd"]
        
        try:
            user = MonchatUser.objects.get(user_name=uname)
        except:
            response = Response({"msg": "Invalid credentials"}, status=404)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        
        if check_password(pwd, user.password):
            sr = serialize_user(user)
            response = Response({"msg": "Signed in succesfully", "data": sr}, status=200)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        else:
            response = Response({"msg": "Invalid credentials"}, status=403)
            response["Access-Control-Allow-Origin"] = "*"
            return response

class Signup(APIView):

    @cors_response
    def post(self, request):
        uname = request.data["uname"]
        pwd = request.data["pwd"]
        pwd = hash_password(pwd)
        new_user_id = generate_id(prefix="user")
        
        try:
            MonchatUser.objects.create(
                user_name=uname,
                user_id=new_user_id,
                user_icon='user.svg',
                password=pwd
            )
        except:
            return Response({"msg": "Error signing up"})

        user = get_object_or_404(
            MonchatUser,
            user_id=new_user_id
        )
        sr = serialize_user(user)

        return Response({"msg": "Signed up sucessfully!", "data": sr}, status=201)

class UserData(APIView):

    @cors_response
    def get(self, request, user_id):
        try:
            user = MonchatUser.objects.get(user_id=user_id)
        except:
            response = Response({"msg": "Invalid credentials"}, status=404)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        
        sr = serialize_user(user)
        return Response({"msg": "Fetched data successfully", "data": sr})

class LatestChats(APIView):

    @cors_response
    def get(self, request, user_id):
        user_qset = get_object_or_404(MonchatUser,
                                      user_id=user_id)
        
        contact_user_ids = set([q.msg_recipient.user_id for q in user_qset.msg_sent.all()] + [q.msg_sender.user_id for q in user_qset.msg_received.all()])
        latest_chat_list = []
        
        for uid in contact_user_ids:
            dt = MonchatMsg.objects.filter(
                            Q(msg_sender__user_id=uid) & Q(msg_recipient__user_id=user_qset.user_id) | Q(msg_recipient__user_id=uid) & Q(msg_sender__user_id=user_qset.user_id)
                        ).latest("msg_time")
            latest_chat_list.append(dt)

        latest_chat_list = [add_msg_fields(q, user_name=user_qset.user_name) for q in json.loads(serializers.serialize('json', latest_chat_list))]

        return Response({"msg": "Fetched data successfully", "data": latest_chat_list}, status=200)

class Chats(APIView):

    @cors_response
    def post(self, request, user_name, recipient):
        new_msg_id = generate_id(prefix='chat')
        msg_sender = get_object_or_404(MonchatUser,
                                      user_name=user_name)
        msg_recipient = get_object_or_404(MonchatUser,
                                      user_id=recipient)
        p = MonchatMsg.objects.create(
            msg_id=new_msg_id,
            msg_body=request.data["msg_body"],
            msg_sender=msg_sender,
            msg_recipient=msg_recipient,
        )

        return Response({"msg": "Saved chat successfully"}, status=201)

    @cors_response
    def get(self, request, user_name, recipient):
        user_data = get_object_or_404(
            MonchatUser,
            user_name=user_name
        )
        conversation_list = MonchatMsg.objects.filter(
                            Q(msg_sender__user_name=recipient) & Q(msg_recipient__user_name=user_name) | Q(msg_recipient__user_name=recipient) & Q(msg_sender__user_name=user_name)
                        ).order_by('msg_time')
        serializer = [add_msg_fields(q, user_name=user_data.user_name) for q in json.loads(serializers.serialize('json', conversation_list))]

        return Response({"msg": "Fetched data succesfully", "data": serializer}, status=200)


class ChatStatus(APIView):

    @cors_response
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
    
class CheckUserName(APIView):

    @cors_response
    def get(self, request, user_name):
        try:
            MonchatUser.objects.get(user_name=user_name)
        except:
            return Response({"msg": "", "data": {"exists": False}}, status=200)
        
        return Response({"msg": "", "data": {"exists": True}}, status=403)