# Generated by Django 4.1.7 on 2023-03-07 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monchat_server_v2', '0002_profileupload_monchatuser_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='monchatuser',
            name='online_status',
            field=models.BooleanField(default=True),
        ),
    ]
