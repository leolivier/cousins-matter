# Generated by Django 5.0.2 on 2024-03-17 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='birthdate',
            field=models.DateField(blank=True, verbose_name='Birthdate'),
        ),
    ]
