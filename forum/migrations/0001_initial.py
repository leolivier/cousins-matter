# Generated by Django 5.0.6 on 2024-05-21 17:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('members', '0006_alter_member_birthdate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(max_length=1048576, verbose_name='Content')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.member')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='Title')),
                ('first_message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='first_of_post', to='forum.message')),
            ],
            options={
                'verbose_name_plural': 'posts',
                'ordering': ['first_message__date'],
            },
        ),
        migrations.AddField(
            model_name='message',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='forum.post'),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True)),
                ('content', models.CharField(max_length=1000, verbose_name='Comment')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='members.member')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forum.message')),
            ],
            options={
                'verbose_name_plural': 'comments',
                'ordering': ['message', 'date'],
                'indexes': [models.Index(fields=['message', 'author'], name='forum_comme_message_e8c1a7_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['title'], name='forum_post_title_46fb82_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['post', 'author'], name='forum_messa_post_id_9ecfe0_idx'),
        ),
    ]
