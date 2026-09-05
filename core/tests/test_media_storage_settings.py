import importlib
import os
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

from config.settings import base


class MediaStorageSettingsTest(SimpleTestCase):
  """Regression test for issue #465: MEDIA_STORAGE must configure the
  "default" STORAGES alias (the one all uploads and media downloads use),
  not the unused "public" alias."""

  def test_default_is_local_filesystem_when_media_storage_unset(self):
    self.assertEqual(
      settings.STORAGES["default"]["BACKEND"],
      "django.core.files.storage.FileSystemStorage",
    )
    self.assertEqual(settings.STORAGES["default"]["OPTIONS"]["location"], settings.MEDIA_ROOT)

  def test_media_storage_configures_default_backend(self):
    env = {
      "MEDIA_STORAGE": "storages.backends.s3.S3Storage",
      "MEDIA_STORAGE_OPTIONS": '{"bucket_name": "test-bucket"}',
    }
    with mock.patch.dict(os.environ, env):
      importlib.reload(base)
      try:
        self.assertEqual(base.STORAGES["default"]["BACKEND"], "storages.backends.s3.S3Storage")
        self.assertEqual(base.STORAGES["default"]["OPTIONS"], {"bucket_name": "test-bucket"})
      finally:
        importlib.reload(base)
