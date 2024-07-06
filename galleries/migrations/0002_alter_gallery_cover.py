# Generated by Django 5.0.6 on 2024-07-06 12:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('galleries', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gallery',
            name='cover',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, 
                                    related_name='cover_of', to='galleries.photo', verbose_name='Cover Photo'),
        ),
    ]
