# Generated by Django 5.0.6 on 2024-06-30 17:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_alter_member_privacy_consent'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='followers',
            field=models.ManyToManyField(blank=True, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Followers'),
        ),
    ]
