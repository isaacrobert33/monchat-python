# Generated by Django 4.1.7 on 2023-03-13 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("monchat_server", "0010_alter_monchatuser_user_bio"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonchatGroup",
            fields=[
                (
                    "group_id",
                    models.SlugField(
                        max_length=256, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("name", models.CharField(default="New Group", max_length=200)),
                ("description", models.TextField(max_length=500)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now_add=True)),
                (
                    "admins",
                    models.ManyToManyField(
                        related_name="group_admin", to="monchat_server.monchatuser"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="groups_created",
                        to="monchat_server.monchatuser",
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(
                        related_name="group_member", to="monchat_server.monchatuser"
                    ),
                ),
            ],
            options={
                "ordering": ["created"],
            },
        ),
    ]
