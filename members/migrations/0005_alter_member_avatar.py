# Generated by Django 5.0.2 on 2024-04-23 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_alter_member_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars'),
        ),
    ]
