import os
import shutil
from django.conf import settings
from django.db import migrations


def mkDirs(apps, schema_editor):
    """Create directories for troves."""
    for dir in [
        settings.TROVE_DIRECTORY,
        settings.TROVE_PICTURE_DIRECTORY,
        settings.TROVE_THUMBNAIL_DIRECTORY,
        settings.TROVE_FILES_DIRECTORY,
    ]:
        os.makedirs(os.path.join(settings.MEDIA_ROOT, dir), exist_ok=True)


def rmDirs(apps, schema_editor):
    """Remove directories for troves."""
    for dir in [
        settings.TROVE_DIRECTORY,
        settings.TROVE_PICTURE_DIRECTORY,
        settings.TROVE_THUMBNAIL_DIRECTORY,
        settings.TROVE_FILES_DIRECTORY,
    ]:
        full_dir = os.path.join(settings.MEDIA_ROOT, dir)
        if os.path.exists(full_dir):
            shutil.rmtree(full_dir)


class Migration(migrations.Migration):
    dependencies = [
        ("troves", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(mkDirs, rmDirs),
    ]
