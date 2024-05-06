# Generated by Django 5.0.2 on 2024-04-21 14:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('galleries', '0006_alter_gallery_parent_alter_gallery_slug_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='gallery',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='galleries.gallery', verbose_name='Gallery'),
        ),
        migrations.AlterField(
            model_name='photo',
            name='name',
            field=models.CharField(blank=True, max_length=70, verbose_name='Name'),
        ),
    ]