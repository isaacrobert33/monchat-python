from datetime import datetime
from django.utils.encoding import smart_str
import hashlib
import random
import uuid

def generate_id(prefix: str):
    return f'{prefix}_{uuid.uuid4().hex}'

def add_msg_fields(data, user_id=None):
    new_data = data["fields"]
    new_data["msg_time"] = new_data["msg_time"].split(".")[0]
    new_data["msg_date"] = datetime.fromisoformat(new_data["msg_time"]).strftime("%Y:%m:%d")
    new_data["msg_time"] = datetime.fromisoformat(new_data["msg_time"]).strftime("%H:%m")
    if user_id:
        new_data["direction"] = "inbound" if new_data["msg_recipient"] == user_id else "outbound"
        
    return new_data


def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")

def hash_password(raw_password):
    algo = 'sha1'
    salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
    hsh = get_hexdigest(algo, salt, raw_password)
    return '%s$%s$%s' % (algo, salt, hsh)

def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    algo, salt, hsh = enc_password.split('$')
    return hsh == get_hexdigest(algo, salt, raw_password)
