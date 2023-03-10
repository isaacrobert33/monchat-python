from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.db.models import Q
from rest_framework.views import APIView
from django.views import View
from rest_framework.response import Response
from .models import MonchatUser, MonchatMsg, ProfileUpload
from .utils import (
    generate_id,
    map_msg_fields,
    check_password,
    hash_password,
    cors_response,
    serialize_user,
    get_chat_socket_id,
    map_unread_count,
)
import json
import traceback

# Create your views here.


class Sigin(APIView):
    @cors_response
    def post(self, request):
        uname = request.data["uname"]
        pwd = request.data["pwd"]

        try:
            user = MonchatUser.objects.get(user_name=uname)
        except:
            return Response({"msg": "Invalid credentials"}, status=404)

        try:
            user_icon = user.profile.latest("uploaded_at").file.name
        except:
            user_icon = "user.svg"

        if check_password(pwd, user.password):
            sr = serialize_user(user)

            return Response(
                {
                    "msg": "Signed in succesfully",
                    "data": {**sr, "user_icon": user_icon},
                },
                status=200,
            )
        else:
            return Response({"msg": "Invalid credentials"}, status=403)


class Signup(APIView):
    @cors_response
    def post(self, request):
        fname = request.data["fname"]
        lname = request.data["lname"]
        uname = request.data["uname"]
        pwd = request.data["pwd"]
        pwd = hash_password(pwd)
        new_user_id = generate_id(prefix="user")

        try:
            MonchatUser.objects.create(
                first_name=fname,
                last_name=lname,
                user_name=uname,
                user_id=new_user_id,
                user_icon="user.svg",
                password=pwd,
            )
        except:
            return Response({"msg": "Error signing up"})

        user = get_object_or_404(MonchatUser, user_id=new_user_id)
        sr = serialize_user(user)

        return Response({"msg": "Signed up sucessfully!", "data": sr}, status=201)


class ResetPwd(APIView):
    def post(self, request):
        uname, pwd = request.data.get("uname"), request.data["pwd"]
        user = get_object_or_404(MonchatUser, user_name=uname)
        user.password = hash_password(pwd)
        user.save()

        return Response(
            {"msg": "Password reset successfully", "data": serialize_user(user)},
            status=200,
        )


class UserData(APIView):
    http_method_names = ["put", "get"]

    @cors_response
    def get(self, request, user_id):
        try:
            user = MonchatUser.objects.get(user_id=user_id)
        except:
            response = Response({"msg": "Invalid credentials"}, status=404)
            response["Access-Control-Allow-Origin"] = "*"
            return response

        sr = serialize_user(user)
        try:
            user_icon = user.profile.latest("uploaded_at").file.name
        except:
            user_icon = "user.svg"

        return Response(
            {"msg": "Fetched data successfully", "data": {**sr, "user_icon": user_icon}}
        )

    def put(self, request, user_id):
        user = get_object_or_404(MonchatUser, user_id=user_id)

        user.first_name = request.data.get("fname", user.first_name)
        user.last_name = request.data.get("lname", user.last_name)
        user.user_bio = request.data.get("user_bio", user.user_bio)
        user.save()

        try:
            user_icon = user.profile.latest("uploaded_at").file.name
        except:
            user_icon = "user.svg"

        return Response(
            {
                "msg": "User profile updated succesfully",
                "data": {**serialize_user(user), "user_icon": user_icon},
            },
            status=200,
        )


class LatestChats(APIView):
    @cors_response
    def get(self, request, user_id):
        user_qset = get_object_or_404(MonchatUser, user_id=user_id)

        contact_user_ids = set(
            [q.msg_recipient.user_id for q in user_qset.msg_sent.all()]
            + [q.msg_sender.user_id for q in user_qset.msg_received.all()]
        )
        latest_chat_list = []

        for uid in contact_user_ids:
            dt = MonchatMsg.objects.filter(
                Q(msg_sender__user_id=uid) & Q(msg_recipient__user_id=user_qset.user_id)
                | Q(msg_recipient__user_id=uid)
                & Q(msg_sender__user_id=user_qset.user_id)
            ).latest("msg_time")
            latest_chat_list.append(dt)

        latest_chat_list = map_msg_fields(
            [q for q in json.loads(serializers.serialize("json", latest_chat_list))],
            user_name=user_qset.user_name,
        )
        latest_chat_list = map_unread_count(latest_chat_list, user_id=user_id)

        return Response(
            {"msg": "Fetched data successfully", "data": latest_chat_list}, status=200
        )


class Chats(APIView):
    @cors_response
    def post(self, request, user_name, recipient):
        new_msg_id = generate_id(prefix="chat")
        msg_sender = get_object_or_404(MonchatUser, user_name=user_name)
        msg_recipient = get_object_or_404(MonchatUser, user_id=recipient)
        p = MonchatMsg.objects.create(
            msg_id=new_msg_id,
            msg_body=request.data["msg_body"],
            msg_sender=msg_sender,
            msg_recipient=msg_recipient,
        )

        return Response({"msg": "Saved chat successfully"}, status=201)

    @cors_response
    def get(self, request, user_name, recipient):
        user_data = get_object_or_404(MonchatUser, user_name=user_name)
        recipient_data = get_object_or_404(MonchatUser, user_name=recipient)
        conversation_list = MonchatMsg.objects.filter(
            Q(msg_sender__user_name=recipient) & Q(msg_recipient__user_name=user_name)
            | Q(msg_recipient__user_name=recipient) & Q(msg_sender__user_name=user_name)
        ).order_by("msg_time")
        excl = ["msg_recipient", "msg_sender", "msg_date"]
        serializer = map_msg_fields(
            [q for q in json.loads(serializers.serialize("json", conversation_list))],
            user_name=user_data.user_name,
            excludes=excl,
            sort=False,
        )

        socket_id = get_chat_socket_id(
            msg_sender=user_data.user_id, msg_recipient=recipient_data.user_id
        )

        return Response(
            {
                "msg": "Fetched data succesfully",
                "data": serializer,
                "socket_id": socket_id,
            },
            status=200,
        )


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


class UserStatus(APIView):
    def get(self, request, user_id):
        user = get_object_or_404(MonchatUser, user_id=user_id)
        return Response(
            {
                "msg": "",
                "data": {
                    "online_status": user.online_status,
                    "last_seen": user.last_seen,
                },
            }
        )


class CheckUserName(APIView):
    @cors_response
    def get(self, request, user_name):
        try:
            MonchatUser.objects.get(user_name=user_name)
        except:
            return Response({"msg": "", "data": {"exists": False}}, status=200)

        return Response({"msg": "", "data": {"exists": True}}, status=403)


class Upload(APIView):
    def post(self, request, user_name):
        user = MonchatUser.objects.get(user_name=user_name)
        file = request.FILES.get("file")
        file.name = f'{user_name}.{file.name.split(".")[1]}'
        fileID = generate_id("file")

        profile = ProfileUpload(file_id=fileID, file=file, user_id=user)
        profile.save()

        return Response({"msg": "File upload succesfully"})


class UserList(APIView):
    def get(self, request, user_id):
        users = MonchatUser.objects.all().exclude(user_id=user_id)
        data = json.loads(serializers.serialize("json", users))

        for i, d in enumerate(data):
            d["fields"].pop("password")
            user_icon = (
                users[i].profile.latest("uploaded_at").file.name
                if users[i].profile.latest("uploaded_at")
                else "user.svg"
            )
            data[i] = {**d["fields"], "user_id": d["pk"], "user_icon": user_icon}

        return Response({"msg": "Fetched data succesfully", "data": data}, status=200)
