import os
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.backup import BackupError, backup_filename, create_dump, prune_local, remote_key, run_backup


class BackupHelpersTests(SimpleTestCase):
  def test_backup_filename_is_utc_and_sortable(self):
    name = backup_filename(datetime(2026, 11, 27, 13, 5, 9, tzinfo=UTC))
    self.assertEqual(name, "cmm-20261127T130509Z.dump")

  def test_remote_key_uses_prefix(self):
    with self.settings(BACKUP_S3_PREFIX="db-backups/"):
      self.assertEqual(remote_key("cmm-x.dump"), "db-backups/cmm-x.dump")
    with self.settings(BACKUP_S3_PREFIX=""):
      self.assertEqual(remote_key("cmm-x.dump"), "cmm-x.dump")

  def test_prune_local_keeps_recent_dumps(self):
    with tempfile.TemporaryDirectory() as tmp:
      directory = Path(tmp)
      old = directory / "cmm-20260101T000000Z.dump"
      recent = directory / "cmm-20261126T000000Z.dump"
      unrelated = directory / "keep-me.txt"
      for path in (old, recent, unrelated):
        path.write_bytes(b"x")
      old_time = (datetime.now(UTC) - timedelta(days=30)).timestamp()
      os.utime(old, (old_time, old_time))
      removed = prune_local(directory, keep_days=14)
      self.assertEqual(removed, 1)
      self.assertFalse(old.exists())
      self.assertTrue(recent.exists())
      self.assertTrue(unrelated.exists())


class CreateDumpTests(SimpleTestCase):
  def _fake_run(self, target: Path):
    def run(command, **kwargs):
      if command[0] == "pg_dump":
        target.write_bytes(b"x" * 4096)
      return subprocess.CompletedProcess(command, 0, "", "")

    return run

  def test_create_dump_runs_pg_dump_then_verifies(self):
    with tempfile.TemporaryDirectory() as tmp:
      target = Path(tmp) / "cmm-test.dump"
      calls = []

      def run(command, **kwargs):
        calls.append(command)
        return self._fake_run(target)(command, **kwargs)

      with patch("core.backup.subprocess.run", side_effect=run):
        result = create_dump(target)
      self.assertEqual(result, target)
      self.assertEqual(calls[0][0], "pg_dump")
      self.assertEqual(calls[1][0], "pg_restore")
      self.assertIn("--format=custom", calls[0])

  def test_create_dump_removes_partial_file_on_failure(self):
    with tempfile.TemporaryDirectory() as tmp:
      target = Path(tmp) / "cmm-test.dump"
      error = subprocess.CalledProcessError(1, ["pg_dump"], stderr="boom")
      with patch("core.backup.subprocess.run", side_effect=error), self.assertRaises(BackupError):
        create_dump(target)
      self.assertFalse(target.exists())


class RunBackupTests(SimpleTestCase):
  def test_run_backup_without_bucket_stays_local(self):
    with tempfile.TemporaryDirectory() as tmp:

      def fake_dump(target, timeout=3600):
        target.write_bytes(b"x" * 2048)
        return target

      with (
        override_settings(BACKUP_DIR=tmp, BACKUP_S3_BUCKET="", BACKUP_KEEP_DAYS=14),
        patch("core.backup.create_dump", side_effect=fake_dump),
      ):
        report = run_backup(now=datetime(2026, 11, 27, tzinfo=UTC))
      self.assertTrue(Path(report["file"]).exists())
      self.assertIsNone(report["uploaded"])
      self.assertEqual(report["bytes"], 2048)
