import logging
import os
import shutil
from unittest.mock import MagicMock

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError
from django.test import TestCase, RequestFactory
from django.utils import translation

from core.utils import (
  assert_request_is_ajax,
  parse_locale_date,
  storage_rmtree,
  temporary_log_level,
  translate_date_format,
  _fs_rmtree,
  _recursive_rmtree,
  _rm_emty_folders,
  protected_media_url,
)


class TestAssertRequestIsAjax(TestCase):
  """Tests for assert_request_is_ajax."""

  def test_non_ajax_request_raises(self):
    """Test that a non-AJAX request raises ValidationError."""
    request = RequestFactory().get("/dummy")
    with self.assertRaises(ValidationError):
      assert_request_is_ajax(request)

  def test_ajax_request_passes(self):
    """Test that an AJAX request does not raise."""
    request = RequestFactory().get("/dummy", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    # Should not raise
    assert_request_is_ajax(request)


class TestTemporaryLogLevel(TestCase):
  """Tests for temporary_log_level context manager."""

  def test_changes_and_restores_log_level(self):
    """Test that level is changed inside context and restored after."""
    test_logger = logging.getLogger("test.temporary_level")
    test_logger.setLevel(logging.WARNING)

    with temporary_log_level(test_logger, logging.DEBUG):
      self.assertEqual(test_logger.level, logging.DEBUG)

    self.assertEqual(test_logger.level, logging.WARNING)


class TestParseLocaleDate(TestCase):
  """Tests for parse_locale_date error path."""

  def test_invalid_date_raises_validation_error(self):
    """Test that an invalid date string raises ValidationError."""
    with self.assertRaises(ValidationError):
      parse_locale_date("not-a-date-at-all")


class TestTranslateDateFormatEdgeCases(TestCase):
  """Tests for translate_date_format edge cases."""

  def test_double_percent(self):
    """Test that %% is translated to a literal %."""
    with translation.override("en"):
      result = translate_date_format("100%%")
      self.assertEqual(result, "100%")

  def test_unknown_format_code(self):
    """Test that an unknown format code like %Z is kept as is."""
    with translation.override("en"):
      result = translate_date_format("%Z")
      self.assertEqual(result, "%Z")

  def test_trailing_percent(self):
    """Test that a single % at the end of string is kept as is."""
    with translation.override("en"):
      result = translate_date_format("test%")
      self.assertEqual(result, "test%")


class TestProtectedMediaUrl(TestCase):
  """Tests for protected_media_url edge cases."""

  def test_with_media_root_prefix(self):
    """Test media path that starts with MEDIA_ROOT."""
    media_root = str(settings.MEDIA_ROOT)
    result = protected_media_url(f"{media_root}/test_file.jpg")
    self.assertIn("test_file.jpg", result)

  def test_with_base_dir_media_prefix(self):
    """Test media path that starts with BASE_DIR/MEDIA_REL."""
    base_media = str(settings.BASE_DIR / settings.MEDIA_REL)
    result = protected_media_url(f"{base_media}/test_file.jpg")
    self.assertIn("test_file.jpg", result)


class TestStorageRmtree(TestCase):
  """Tests for storage_rmtree and helper functions."""

  def test_empty_prefix_aborts(self):
    """Test that empty prefix aborts without error."""
    storage = MagicMock()
    storage_rmtree(storage, "")
    storage.delete.assert_not_called()

  def test_slash_prefix_aborts(self):
    """Test that slash-only prefix aborts without error."""
    storage = MagicMock()
    storage_rmtree(storage, "/")
    storage.delete.assert_not_called()

  def test_fs_rmtree_with_filesystem_storage(self):
    """Test _fs_rmtree with FileSystemStorage."""
    test_dir = settings.MEDIA_ROOT / "test_coverage_rmtree"
    os.makedirs(test_dir, exist_ok=True)
    try:
      storage = FileSystemStorage()
      result = _fs_rmtree(storage, "test_coverage_rmtree")
      self.assertTrue(result)
      self.assertFalse(os.path.isdir(test_dir))
    finally:
      if os.path.isdir(test_dir):
        shutil.rmtree(test_dir)

  def test_fs_rmtree_nonexistent_dir(self):
    """Test _fs_rmtree with non-existent directory still returns True."""
    storage = FileSystemStorage()
    result = _fs_rmtree(storage, "nonexistent_dir_xyz_coverage")
    self.assertTrue(result)

  def test_fs_rmtree_non_filesystem_storage(self):
    """Test _fs_rmtree returns False for non-FileSystemStorage."""
    storage = MagicMock(spec=[])  # mock without FileSystemStorage interface
    result = _fs_rmtree(storage, "prefix")
    self.assertFalse(result)

  def test_rm_empty_folders(self):
    """Test _rm_emty_folders processes folder stack."""
    storage = MagicMock()
    storage.delete.side_effect = [None, Exception("not empty")]
    _rm_emty_folders(storage, ["folder1", "folder2"])
    self.assertEqual(storage.delete.call_count, 2)

  def test_recursive_rmtree(self):
    """Test _recursive_rmtree with mock storage."""
    storage = MagicMock()
    # First call returns files and dirs, second call returns empty
    storage.listdir.side_effect = [
      (["subdir"], ["file1.txt", "file2.txt"]),
      ([], ["file3.txt"]),
    ]
    _recursive_rmtree(storage, "prefix")
    # Should have deleted 3 files total
    self.assertTrue(storage.delete.call_count >= 3)

  def test_storage_rmtree_no_listdir(self):
    """Test storage_rmtree with storage that has no listdir."""
    storage = MagicMock(spec=["delete"])  # no listdir
    # Not a FileSystemStorage so _fs_rmtree returns False
    storage_rmtree(storage, "some_prefix")
    storage.delete.assert_called_once_with("some_prefix/")
