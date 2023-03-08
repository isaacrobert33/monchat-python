import json, traceback
from .models import MonchatMsg
from .utils import save_msg_to_db
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import MonchatUser, MonchatMsg
from django.db.models import Q
from .utils import generate_id
from datetime import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["tunnel_id"]

        self.room_group_name = "chat__%s" % self.room_name
        print(self.channel_name, self.room_group_name)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        msg_data = json.loads(text_data)
        print(msg_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", **msg_data}
        )

        await self.save_msg_to_db(**msg_data)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, code):
        self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def save_msg_to_db(self, msg_body, msg_sender, msg_recipient, msg_time):
        new_msg_id = generate_id(prefix="chat")
        msg_recipient = MonchatUser.objects.get(user_name=msg_recipient.strip("'"))
        msg_sender = MonchatUser.objects.get(user_name=msg_sender.strip("'"))
        msg_time = datetime.fromisoformat(msg_time.split(".")[0])

        try:
            MonchatMsg.objects.create(
                msg_id=new_msg_id,
                msg_body=msg_body,
                msg_sender=msg_sender,
                msg_recipient=msg_recipient,
                msg_time=msg_time,
            )
        except:
            print(traceback.format_exc())

        self.update_msg_status(
            msg_recipient=msg_recipient, msg_sender=msg_sender, msg_time=msg_time
        )

    def update_msg_status(self, msg_sender, msg_recipient, msg_time):
        msgs = MonchatMsg.objects.filter(
            Q(msg_status=MonchatMsg.MsgStatus.UNDELIVERED)
            | Q(msg_status=MonchatMsg.MsgStatus.DELIVERED),
            msg_time__lte=msg_time,
            msg_recipient=msg_recipient,
            msg_sender=msg_sender,
        )
        for msg in msgs:
            msg.msg_status = MonchatMsg.MsgStatus.READ
            msg.save()

        print("Updated", msgs.count())


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "user"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        user_name = data["user_name"]
        connection_type = data["type"]
        print(user_name, connection_type)
        await self.change_online_status(user_name, connection_type)

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
    def change_online_status(self, user_name, c_type):
        userprofile = MonchatUser.objects.get(user_name=user_name)

        if c_type == "open":
            userprofile.online_status = True
            userprofile.save()
        else:
            userprofile.online_status = False
            userprofile.save()
        print("Status updated")


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
