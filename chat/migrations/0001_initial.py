# Generated by Django 5.0.6 on 2024-05-25 15:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=2097152, verbose_name='message')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('date_added',),
            },
        ),
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(max_length=255)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'salle de chat',
                'verbose_name_plural': 'salles de chat',
                'ordering': ('date_added',),
                'indexes': [models.Index(fields=['slug'], name='chat_chatro_slug_23d243_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='chatroom',
            constraint=models.UniqueConstraint(fields=('slug',), name='chat room slugs must be unique'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.chatroom'),
        ),
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['room'], name='chat_chatme_room_id_95b551_idx'),
        ),
    ]