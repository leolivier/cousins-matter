# Generated by Django 5.0.7 on 2024-07-31 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_privatechatroom'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='chatroom',
            name='chat room slugs must be unique',
        ),
        migrations.AlterField(
            model_name='chatroom',
            name='slug',
            field=models.CharField(blank=True, max_length=255, unique=True),
        ),
    ]
