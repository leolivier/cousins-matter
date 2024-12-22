# Generated by Django 5.1.1 on 2024-12-14 16:01

import galleries.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('galleries', '0002_alter_gallery_cover'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='image_height',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='photo',
            name='image_width',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(height_field='image_height', max_length=1000, upload_to=galleries.models.photo_path, validators=[galleries.models.check_image_size], verbose_name='Photo', width_field='image_width'),
        ),
        migrations.AlterModelOptions(
            name='photo',
            options={'ordering': ['id']},
        ),
    ]