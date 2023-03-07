import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # accept connection
        self.accept()
    def disconnect(self, close_code):
        pass
            
    # receive message from WebSocket
    def receive(self, msg_data):
        text_data_json = json.loads(msg_data)
        message = text_data_json['message']
        msg_data = {}
        # send message to WebSocket 
        self.send(text_data=json.dumps({'message': message}))

        