import json, traceback, pytz
from .models import MonchatMsg
from .utils import save_msg_to_db
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import MonchatUser, MonchatMsg, MonchatGroup
from django.db.models import Q
from .utils import check_members_read
from datetime import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["tunnel_id"]

        self.room_group_name = "chat__%s" % self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        msg_data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", **msg_data}
        )

        await self.save_msg_to_db(**msg_data)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, code):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def save_msg_to_db(
        self, msg_id, msg_body, msg_sender, msg_recipient, msg_time, **kwargs
    ):
        tz = pytz.timezone("UTC")
        msg_recipient = MonchatUser.objects.get(user_name=msg_recipient.strip("'"))
        msg_sender = MonchatUser.objects.get(user_name=msg_sender.strip("'"))
        msg_time = tz.localize(datetime.fromisoformat(msg_time.split(".")[0]))

        try:
            MonchatMsg.objects.create(
                msg_id=msg_id,
                msg_body=msg_body,
                msg_sender=msg_sender,
                msg_recipient=msg_recipient,
                msg_time=msg_time,
                msg_status=MonchatMsg.MsgStatus.DELIVERED
                if msg_recipient.online_status
                else MonchatMsg.MsgStatus.UNDELIVERED,
            )
        except:
            print(traceback.format_exc())


class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["group_id"]

        self.room_group_name = "group__%s" % self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        msg_data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "group_chat", **msg_data}
        )

        await self.save_msg_to_db(**msg_data)

    async def group_chat(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, code):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def save_msg_to_db(
        self, msg_id, msg_body, msg_sender, group_id, msg_time, **kwargs
    ):
        msg_sender = MonchatUser.objects.get(user_name=msg_sender.strip("'"))
        msg_time = datetime.fromisoformat(msg_time.split(".")[0])

        try:
            msg = MonchatMsg.objects.create(
                msg_id=msg_id,
                msg_body=msg_body,
                msg_sender=msg_sender,
                msg_recipient=msg_sender,
                group_id=group_id,
                msg_time=msg_time,
                msg_status=MonchatMsg.MsgStatus.UNDELIVERED,
            )
            msg.read_by.add(msg_sender)
        except:
            print(traceback.format_exc())


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "user"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user_name = data["user_name"]
        connection_type = data["type"]
        time = data.get("time", "")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_status",
                "user_name": user_name,
                "online_status": True if connection_type == "open" else False,
                "time": time,
            },
        )
        await self.change_online_status(user_name, connection_type, time)

    async def online_status(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_onlineStatus(self, event):
        data = json.loads(event.get("value"))
        user_name = data["user_name"]
        online_status = data["status"]

        await self.send(
            text_data=json.dumps(
                {"user_name": user_name, "online_status": online_status}
            )
        )

    async def disconnect(self, message):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def change_online_status(self, user_name, c_type, time=None):
        userprofile = MonchatUser.objects.get(user_name=user_name)
        print(user_name, c_type, time)

        if c_type == "open":
            userprofile.online_status = True
            userprofile.save()
        else:
            userprofile.online_status = False
            userprofile.last_seen = (
                datetime.fromisoformat(time.split(".")[0])
                if time
                else userprofile.last_seen
            )
            userprofile.save()

        print("Status updated")


class ReadRecieptConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = self.scope["url_route"]["kwargs"]["chat_id"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_status_change", **data}
        )
        await self.change_msg_status(**data)

    async def chat_status_change(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, code):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def change_msg_status(self, msg_id, msg_status, read_time, **kwargs):
        msg_data = MonchatMsg.objects.get(msg_id=msg_id)
        msg_data.read_time = datetime.fromisoformat(read_time.split(".")[0])

        if kwargs.get("read_by"):
            user = MonchatUser.objects.get(user_name=kwargs["read_by"])
            msg_data.read_by.add(user)
            msg_data.save()

            if check_members_read(msg_data, msg_data.group_id):
                msg_data.msg_status = msg_status
                msg_data.save()

        else:
            msg_data.msg_status = msg_status
            msg_data.save()

        if kwargs:
            self.update_msg_status(
                msg_recipient=kwargs.get("msg_recipient"),
                msg_sender=kwargs.get("msg_sender"),
                msg_time=msg_data.msg_time,
            )

    def update_msg_status(self, msg_sender, msg_recipient, msg_time):
        msgs = MonchatMsg.objects.filter(
            Q(msg_status=MonchatMsg.MsgStatus.UNDELIVERED)
            | Q(msg_status=MonchatMsg.MsgStatus.DELIVERED),
            msg_time__lte=msg_time,
            msg_recipient__user_name=msg_recipient,
            msg_sender__user_name=msg_sender,
        )
        for msg in msgs:
            msg.msg_status = MonchatMsg.MsgStatus.READ
            msg.save()

class StatusUpdate(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = self.scope["url_route"]["kwargs"]["chat_id"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def receive(self):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "post_status", **data}
        )
        await self.change_msg_status(**data)

    async def disconnect(self, code):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def post_status(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def save_status(self, **kwargs):
        pass 





# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         my_id = self.scope['user'].id
#         self.room_group_name = f'{my_id}'
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, code):
#         self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def send_notification(self, event):
#         data = json.loads(event.get('value'))
#         count = data['count']
#         print(count)
#         await self.send(text_data=json.dumps({
#             'count': count
#         }))
