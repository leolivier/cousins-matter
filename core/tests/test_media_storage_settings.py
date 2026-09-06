import importlib
import os
from unittest import mock

from django.test import SimpleTestCase

from config.settings import base


class MediaStorageSettingsTest(SimpleTestCase):
  """Regression test for issue #465: MEDIA_STORAGE must configure the
  "default" STORAGES alias (the one all uploads and media downloads use),
  not the unused "public" alias."""

  def test_default_is_local_filesystem_when_media_storage_unset(self):
    # Hermetic: purge MEDIA_STORAGE even if the CI environment exports it
    # (e.g. the S3-mode CI job) instead of relying on it being unset.
    with mock.patch.dict(os.environ):
      os.environ.pop("MEDIA_STORAGE", None)
      os.environ.pop("MEDIA_STORAGE_OPTIONS", None)
      try:
        importlib.reload(base)
        self.assertEqual(
          base.STORAGES["default"]["BACKEND"],
          "django.core.files.storage.FileSystemStorage",
        )
        self.assertEqual(base.STORAGES["default"]["OPTIONS"]["location"], base.MEDIA_ROOT)
      finally:
        importlib.reload(base)

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
