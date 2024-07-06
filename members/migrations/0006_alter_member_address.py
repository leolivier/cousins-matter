# Generated by Django 5.0.6 on 2024-07-06 12:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_member_followers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.address', verbose_name='Address'),
        ),
    ]
