# Generated by Django 5.1.1 on 2024-11-10 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_alter_member_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='deathdate',
            field=models.DateField(blank=True, null=True, verbose_name='Death date'),
        ),
        migrations.AddField(
            model_name='member',
            name='is_dead',
            field=models.BooleanField(default=False, verbose_name='Is dead'),
        ),
    ]