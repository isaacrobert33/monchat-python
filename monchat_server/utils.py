from datetime import datetime
from .models import MonchatUser, MonchatMsg, MonchatGroup
from django.core.serializers import serialize
from django.db.models import Q
from django.utils.encoding import smart_str
from datetime import datetime
from functools import wraps
import timeago
import hashlib
import json
import traceback
import random
import uuid
import pytz


def generate_id(prefix: str):
    return f"{prefix}_{uuid.uuid4().hex}"


def serialize_user(queryset, extra={}):
    data = json.loads(serialize("json", [queryset]))[0]
    data["fields"].pop("password")
    return {**data["fields"], **{"user_id": data["pk"], **extra}}


def serialize_group(queryset: list, single=False):
    data = json.loads(serialize("json", queryset))
    data = [{**d["fields"], "group_id": d["pk"]} for d in data]

    for i, d in enumerate(data):
        data[i]["group_icon"] = (
            queryset[i].icon.latest("uploaded_at").file.name
            if queryset[i].icon.first()
            else ""
        )

    return data[0] if single else data


def map_group_unread_count(group_chat, user_id):
    grp = MonchatMsg.objects.exclude(read_by__user_id=user_id).filter(
        group_id=group_chat["group_id"]
    )
    mapped = {**group_chat, "unread_count": grp.count()}

    return mapped


def sort_chats(chats: list, user_id, date_format="iso") -> list:
    tz = pytz.timezone("UTC")
    chats_data = chats

    # Removal of self messages
    for chat in chats:
        if (
            not chat["type"] in ["group_info", "group_chat"]
            and chat["msg_sender"]["user_id"] == chat["msg_recipient"]["user_id"]
        ):
            chats_data.remove(chat)

    return sorted(
        chats_data,
        key=lambda x: datetime.fromisoformat(str(x["msg_date"]))
        if datetime.fromisoformat(str(x["msg_date"]).split(".")[0]).tzinfo
        else tz.localize(datetime.fromisoformat(str(x["msg_date"]).split(".")[0])),
        reverse=True,
    )


def user_group_chats(groups, user_id):
    chats = []
    tz = pytz.timezone("UTC")

    for group in groups:
        latest_chat = MonchatMsg.objects.filter(group_id=group.group_id).latest(
            "msg_time"
        )
        group_json_data = json.loads(serialize("json", [group]))[0]

        if latest_chat:
            json_data = json.loads(serialize("json", [latest_chat]))[0]
            sender_data = MonchatUser.objects.get(
                user_id=json_data["fields"]["msg_sender"]
            )
            sender_user_icon = (
                sender_data.profile.latest("uploaded_at").file.name
                if sender_data.profile.all()
                else "user.svg"
            )
            sender_data = serialize_user(sender_data, {"user_icon": sender_user_icon})
            sender_data["user_name"] = (
                "You" if sender_data["user_id"] == user_id else sender_data["user_name"]
            )

            d = {
                "group_data": {
                    **group_json_data["fields"],
                    "group_icon": group.icon.latest("uploaded_at").file.name
                    if group.icon.first()
                    else "",
                    "group_id": group.group_id,
                    "members": [m.user_name for m in group.members.all()],
                },
                **json_data["fields"],
                "msg_date": json_data["fields"]["msg_time"],
                "msg_timeago": timeago.format(
                    tz.localize(
                        datetime.fromisoformat(
                            json_data["fields"]["msg_time"].split(".")[0]
                        )
                    ),
                    now=tz.localize(datetime.now()),
                ),
                "msg_time": datetime.fromisoformat(
                    json_data["fields"]["msg_time"].split(".")[0]
                ).strftime("%H:%M"),
                "msg_sender": sender_data,
                "direction": "outbound"
                if latest_chat.msg_sender.user_id == user_id
                else "inbound",
                "type": "group_chat",
            }
            d = map_group_unread_count(
                d, user_id=user_id
            )  ## Map unread count for group msg
            chats.append(d)
        else:
            d = {
                "msg_time": group.created.strftime("%H:%M"),
                "msg_timeago": timeago.format(
                    group.created, now=tz.localize(datetime.now())
                ),
                "msg_date": group.created,
                "group_data": {
                    **group_json_data["fields"],
                    "group_icon": group.icon.latest("uploaded_at").file.name
                    if group.icon.first()
                    else "",
                    "group_id": group_json_data["pk"],
                    "members": [m.user_name for m in group.members.all()],
                    "info": f'You created this group "{group.name}"'
                    if group.created_by.user_id == user_id
                    else f"This group was created by {group.created_by.user_name}",
                },
                "type": "group_info",
                "unread_count": 0,
            }
            chats.append(d)

    return chats


def new_group_data(group, user_id: str) -> dict:
    tz = pytz.timezone("UTC")
    group_json_data = json.loads(serialize("json", [group]))[0]
    data = {
        "msg_time": group.created.strftime("%H:%M"),
        "msg_timeago": timeago.format(group.created, now=tz.localize(datetime.now())),
        "msg_date": group.created,
        "group_data": {
            **group_json_data["fields"],
            "group_icon": group.icon.latest("uploaded_at").file.name
            if group.icon.first()
            else "",
            "group_id": group_json_data["pk"],
            "members": [m.user_name for m in group.members.all()],
            "info": f'You created this group "{group.name}"'
            if group.created_by.user_id == user_id
            else f"This group was created by {group.created_by.user_name}",
        },
        "type": "group_info",
        "unread_count": 0,
    }
    return data


def map_msg_fields(
    msg_data: list,
    user_name: str,
    excludes=[],
    sort=True,
    extra_user_data=True,
    chat_type="single_chat",
) -> list:
    mapped = []

    # Sort the data if the sort parameter is True
    if sort:
        msg_data = sorted(
            msg_data,
            key=lambda x: datetime.fromisoformat(x["fields"]["msg_time"].split(".")[0]),
            reverse=True,
        )

    for data in msg_data:
        new_data = data["fields"]

        # Get the recipient data and user icon
        recp_data = MonchatUser.objects.get(user_id=new_data["msg_recipient"])
        recp_user_icon = (
            recp_data.profile.latest("uploaded_at").file.name
            if recp_data.profile.all()
            else "user.svg"
        )
        recp_data = serialize_user(recp_data, {"user_icon": recp_user_icon})

        # Format the msg_time and msg_timeago fields
        new_data["msg_time"] = datetime.fromisoformat(
            new_data["msg_time"].split(".")[0]
        )
        new_data["msg_timeago"] = timeago.format(
            new_data["msg_time"], now=datetime.now()
        )
        new_data["msg_date"] = new_data["msg_time"]
        new_data["msg_time"] = new_data["msg_time"].strftime("%H:%M")

        # Get the sender data and user icon
        sender_data = MonchatUser.objects.get(user_id=new_data["msg_sender"])
        sender_user_icon = (
            sender_data.profile.latest("uploaded_at").file.name
            if sender_data.profile.all()
            else "user.svg"
        )
        new_data["msg_sender"] = serialize_user(
            sender_data, {"user_icon": sender_user_icon}
        )

        # Set the recipient data and msg_id
        new_data["msg_recipient"] = recp_data
        new_data["msg_id"] = data["pk"]

        # Set the direction field if user_name is provided
        if user_name:
            new_data["direction"] = (
                "outbound"
                if new_data["msg_sender"]["user_name"] == user_name
                else "inbound"
            )

        # Set the msg_sender and msg_recipient fields to user_name if extra_user_data is False
        if not extra_user_data:
            new_data["msg_sender"] = new_data["msg_sender"]["user_name"]
            new_data["msg_recipient"] = new_data["msg_recipient"]["user_name"]

        # Set the chat_type field
        new_data["type"] = chat_type

        # Remove excluded fields
        for f in excludes:
            new_data.pop(f)

        mapped.append(new_data)

    return mapped


def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    raw_password, salt = smart_str(raw_password), smart_str(salt)

    if algorithm == "crypt":
        try:
            import crypt
        except ImportError:
            raise ValueError(
                '"crypt" password algorithm not supported in this environment'
            )
        return crypt.crypt(raw_password, salt)

    if algorithm == "md5":
        return hashlib.md5(salt.encode() + raw_password.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(salt.encode() + raw_password.encode()).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")


def hash_password(raw_password: str):
    algo = "sha1"
    salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest(algo, salt, raw_password)
    return "%s$%s$%s" % (algo, salt, hsh)


def check_password(raw_password: str, enc_password: str):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    algo, salt, hsh = enc_password.split("$")
    return hsh == get_hexdigest(algo, salt, raw_password)


def cors_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        f = func(*args, **kwargs)
        f["Access-Control-Allow-Origin"] = "*"
        return f

    return wrapper


def update_msg_status(msg_sender: str, msg_recipient: str, msg_time):
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
    print(f"Updated read status of {msgs.count()} messages")
    return True


def save_msg_to_db(msg_body: str, msg_sender: str, msg_recipient: str, msg_time):
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
        return False

    update_msg_status(
        msg_recipient=msg_recipient, msg_sender=msg_sender, msg_time=msg_time
    )
    return True


def get_chat_socket_id(msg_sender: str, msg_recipient: str):
    socket_id = "__".join(sorted([msg_sender, msg_recipient]))
    return socket_id


def map_unread_count(data: list, user_id: str, group: bool=False):
    mapped = []

    for msg in data:
        if group:
            unread_count = MonchatMsg.objects.filter(read_by__user_id=user_id).count()
        else:
            recp = (
                msg["msg_sender"]["user_id"]
                if msg["direction"] == "inbound"
                else msg["msg_recipient"]["user_name"]
            )
            unread_count = MonchatMsg.objects.filter(
                Q(msg_status=MonchatMsg.MsgStatus.UNDELIVERED)
                | Q(msg_status=MonchatMsg.MsgStatus.DELIVERED),
                msg_sender__user_id=recp,
                msg_recipient__user_id=user_id,
            ).count()
        msg["unread_count"] = unread_count
        mapped.append(msg)

    return mapped


def check_members_read(msg_data: str, group_id: str):
    group = MonchatGroup.objects.get(group_id=group_id)
    return msg_data.read_by.count() == group.members.count()
