from datetime import datetime
import uuid

def generate_id(prefix: str):
    return f'{prefix}_{uuid.uuid4().hex}'

def add_msg_fields(data):
    new_data = data["fields"]
    new_data["msg_time"] = new_data["msg_time"].split(".")[0]
    new_data["msg_date"] = datetime.fromisoformat(new_data["msg_time"]).strftime("%Y:%m:%d")
    new_data["msg_time"] = datetime.fromisoformat(new_data["msg_time"]).strftime("%H:%m")
    
    return new_data

