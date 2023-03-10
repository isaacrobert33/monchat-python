from datetime import datetime
from .models import MonchatUser, MonchatMsg
from django.core.serializers import serialize
from django.db.models import Q
from django.utils.encoding import smart_str
from datetime import datetime
from functools import wraps
import hashlib
import json
import traceback
import random
import uuid


def generate_id(prefix: str):
    return f"{prefix}_{uuid.uuid4().hex}"


def serialize_user(queryset, extra={}):
    data = json.loads(serialize("json", [queryset]))[0]
    data["fields"].pop("password")
    return {**data["fields"], **{"user_id": data["pk"], **extra}}


def map_msg_fields(
    msg_data: list, user_name: str, excludes=[], sort=True, extra_user_data=True
) -> list:
    mapped = []
    msg_data = (
        sorted(
            msg_data,
            key=lambda x: datetime.fromisoformat(x["fields"]["msg_time"].split(".")[0]),
            reverse=True,
        )
        if sort
        else msg_data
    )

    for data in msg_data:
        new_data = data["fields"]
        recp_data = MonchatUser.objects.get(user_id=new_data["msg_recipient"])
        profile_data = recp_data.profile.latest("uploaded_at")
        recp_user_icon = "user.svg" if not profile_data else profile_data.file.name

        recp_data = serialize_user(recp_data, {"user_icon": recp_user_icon})
        new_data["msg_time"] = datetime.fromisoformat(
            new_data["msg_time"].split(".")[0]
        )
        new_data["msg_date"] = new_data["msg_time"].strftime("%Y:%m:%d")
        new_data["msg_time"] = new_data["msg_time"].strftime("%H:%M")
        sender_data = MonchatUser.objects.get(user_id=new_data["msg_sender"])
        profile_data = sender_data.profile.latest("uploaded_at")
        sender_user_icon = profile_data.file.name if profile_data else "user.svg"

        new_data["msg_sender"] = serialize_user(
            sender_data, {"user_icon": sender_user_icon}
        )

        new_data["msg_recipient"] = recp_data
        new_data["msg_id"] = data["pk"]

        if user_name:
            new_data["direction"] = (
                "outbound"
                if new_data["msg_sender"]["user_name"] == user_name
                else "inbound"
            )

        if not extra_user_data:
            new_data["msg_sender"] = new_data["msg_sender"]["user_name"]
            new_data["msg_recipient"] = new_data["msg_recipient"]["user_name"]

        # Removing excluded fields
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
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(salt.encode() + raw_password.encode()).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")


def hash_password(raw_password):
    algo = "sha1"
    salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest(algo, salt, raw_password)
    return "%s$%s$%s" % (algo, salt, hsh)


def check_password(raw_password, enc_password):
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


def update_msg_status(msg_sender, msg_recipient, msg_time):
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


def save_msg_to_db(msg_body, msg_sender, msg_recipient, msg_time):
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


def get_chat_socket_id(msg_sender, msg_recipient):
    socket_id = "__".join(sorted([msg_sender, msg_recipient]))
    return socket_id


def map_unread_count(data: list, user_id):
    mapped = []

    for msg in data:
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
