# Generated by Django 4.1.7 on 2023-03-07 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monchat_server_v2', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='profile_assets/%Y/%m/%d/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='monchatuser',
            name='first_name',
            field=models.CharField(default=models.CharField(max_length=256), max_length=200),
        ),
        migrations.AddField(
            model_name='monchatuser',
            name='last_name',
            field=models.CharField(default=models.CharField(max_length=256), max_length=200),
        ),
    ]
