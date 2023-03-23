from django.db import models

# Create your models here.


class MonchatUser(models.Model):
    user_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    user_name = models.CharField(max_length=256)
    first_name = models.CharField(max_length=200, default=user_name)
    last_name = models.CharField(max_length=200, default=user_name)
    user_icon = models.CharField(max_length=356)
    password = models.TextField(max_length=256, default="<no-password>")
    online_status = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now_add=True)
    user_bio = models.TextField(max_length=150, default="Hey there, I'm using MonChat")

    def default_name(self):
        return self.user_name.upper()

    def save(self, *args, **kwargs):
        if not self.first_name:
            self.first_name = self.default_name()
        if not self.last_name:
            self.last_name = self.default_name()

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.user_name


class MonchatGroup(models.Model):
    group_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    name = models.CharField(max_length=200, default="New Group")
    description = models.TextField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        MonchatUser,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="groups_created",
    )
    admins = models.ManyToManyField("MonchatUser", related_name="group_admin")
    members = models.ManyToManyField("MonchatUser", related_name="group_member")

    class Meta:
        ordering = ["created"]

    def __str__(self) -> str:
        return self.name


class MonchatMsg(models.Model):
    class MsgStatus(models.TextChoices):
        READ = "RD", "Read"
        DELIVERED = "DV", "Delivered"
        UNDELIVERED = "UD", "Undelivered"

    msg_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    msg_body = models.TextField()
    msg_time = models.DateTimeField(auto_now_add=True)
    read_time = models.DateTimeField(auto_now_add=True)
    msg_sender = models.ForeignKey(
        MonchatUser,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="msg_sent",
    )
    msg_recipient = models.ForeignKey(
        MonchatUser,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="msg_received",
        blank=True,
    )
    msg_status = models.CharField(
        max_length=2, choices=MsgStatus.choices, default=MsgStatus.UNDELIVERED
    )
    group_id = models.CharField(max_length=256, default="")

    read_by = models.ManyToManyField(
        "MonchatUser", related_name="group_msg_read", blank=True
    )

    class Meta:
        ordering = ["msg_time"]

    def __str__(self) -> str:
        return f"<{self.msg_sender}> to <{self.msg_recipient}>"


class ProfileUpload(models.Model):
    file_id = models.SlugField(
        max_length=256, unique=True, primary_key=True, default="<file_id>"
    )
    file = models.FileField(upload_to="%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(
        MonchatUser,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="profile",
        default=MonchatUser,
    )

    def save(self, *args, **kwargs):
        return super(ProfileUpload, self).save(*args, **kwargs)

    def __str__(self):
        return self.file.name


class MonchatGroupUpload(models.Model):
    file_id = models.SlugField(
        max_length=256, unique=True, primary_key=True, default="<file_id>"
    )
    file = models.FileField(upload_to="profiles/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    group_id = models.ForeignKey(
        MonchatGroup,
        to_field="group_id",
        on_delete=models.CASCADE,
        related_name="icon",
        default=MonchatUser,
    )

    def save(self, *args, **kwargs):
        return super(MonchatGroupUpload, self).save(*args, **kwargs)

    def __str__(self):
        return self.group_id.name


class StatusPost(models.Model):
    class StatusType(models.TextChoices):
        VIDEO = "VIDEO", "VD"
        IMAGE = "IMAGE", "IMG"
        VOICE = "VOICE", "VCE"

    status_id = models.SlugField(max_length=256, unique=True, primary_key=True)
    status_file = models.FileField(upload_to="statuses/%Y/%m/%d/")
    status_type = models.CharField(
        max_length=5, choices=StatusType.choices, default=StatusType.IMAGE
    )
    status_user = models.ForeignKey(
        MonchatUser,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    status_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.status}"


# class ContactedUsers(models.Model):
#     user_id = models.ForeignKey(
#         MonchatUser,
#         on_delete=models.CASCADE,
#         related_name='contacts'
#     )

#     def __str__(self) -> str:
#         return self.user_id
