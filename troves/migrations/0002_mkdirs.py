import os
from django.conf import settings
from django.db import migrations

def mkDirs(apps, schema_editor):
    """Create directories for pictures, thumbnails and files. Used by migration 0002_mkdirs"""
    for dir in [settings.TROVE_PICTURE_DIRECTORY,
                settings.TROVE_THUMBNAIL_DIRECTORY,
                settings.TROVE_FILES_DIRECTORY]:
      os.makedirs(os.path.join(settings.MEDIA_ROOT, dir), exist_ok=True)


class Migration(migrations.Migration):

    dependencies = [
        ('troves', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(mkDirs),
    ]
