# Generated by Django 5.1.1 on 2024-12-29 09:47

import pathlib
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Trove',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='Description of the treasure')),
                ('picture', models.ImageField(upload_to=pathlib.PurePosixPath('troves/pictures'),
                                              verbose_name='Treasure photo')),
                ('thumbnail', models.ImageField(blank=True, upload_to=pathlib.PurePosixPath('troves/pictures/thumbnails'))),
                ('file', models.FileField(blank=True, null=True, upload_to=pathlib.PurePosixPath('troves/files'),
                                          verbose_name='Treasure file')),
                ('category', models.CharField(choices=[('history', 'History & Stories'),
                                                       ('recipes', 'Recipes'),
                                                       ('cousinades', 'Family meetings'),
                                                       ('recollections', 'Recollections'),
                                                       ('arts', 'Arts'),
                                                       ('miscellaneous', 'Miscellaneous')
                                                       ],
                                              max_length=20, verbose_name='Category')),
                ('owner', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'trove',
                'verbose_name_plural': 'troves',
                'ordering': ['id'],
                'indexes': [models.Index(fields=['category'], name='troves_trov_categor_900909_idx')],
            },
        ),
    ]
