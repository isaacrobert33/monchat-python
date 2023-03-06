from django.db import models

# Create your models here.

class MonchatUser(models.Model):

    user_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    user_name = models.CharField(max_length=256)
    user_icon = models.CharField(max_length=356)
    password = models.TextField(max_length=256, default="<no-password>")

    def __str__(self) -> str:
        return self.user_name

class MonchatMsg(models.Model):

    class MsgStatus(models.TextChoices):
        READ = 'RD', 'Read'
        DELIVERED = 'DV', 'Delivered'
        UNDELIVERED = 'UD', 'Undelivered'

    msg_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    msg_body = models.TextField()
    msg_time = models.DateTimeField(auto_now_add=True)
    msg_sender = models.ForeignKey(
        MonchatUser,
        to_field='user_id',
        on_delete=models.CASCADE,
        related_name='msg_sent'
    )
    msg_recipient = models.ForeignKey(
        MonchatUser,
        to_field='user_id',
        on_delete=models.CASCADE,
        related_name='msg_received'
    )
    msg_status = models.CharField(max_length=2,
                          choices=MsgStatus.choices,
                          default=MsgStatus.UNDELIVERED)

    class Meta:
        ordering = ['msg_time']

    def __str__(self) -> str:
        return f'<{self.msg_sender}> to <{self.msg_recipient}>'

# class ContactedUsers(models.Model):
#     user_id = models.ForeignKey(
#         MonchatUser,
#         on_delete=models.CASCADE,
#         related_name='contacts'
#     )

#     def __str__(self) -> str:
#         return self.user_id