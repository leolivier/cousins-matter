import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import SimpleTestCase

from core.management.commands.check_okf import check_bundle


def _write(base: Path, rel: str, text: str) -> None:
  p = base / rel
  p.parent.mkdir(parents=True, exist_ok=True)
  p.write_text(text, encoding="utf-8")


class CheckBundleTests(SimpleTestCase):
  def _bundle(self, **files: str) -> Path:
    d = tempfile.TemporaryDirectory()
    self.addCleanup(d.cleanup)
    b = Path(d.name)
    for name, text in files.items():
      _write(b, name, text)
    return b

  def test_conformant_bundle_passes(self) -> None:
    b = self._bundle(**{
      "index.md": "---\ntype: Directory\ntitle: Index\n---\n\n# Index\n",
      "apps/members.md": "---\ntype: App Reference\ntitle: Members\n---\n\n# Members\n",
    })
    self.assertEqual(check_bundle(b), ([], []))

  def test_missing_frontmatter_fails(self) -> None:
    errors, stale = check_bundle(self._bundle(**{"bad.md": "# no frontmatter\n"}))
    self.assertEqual(errors, ["bad.md: missing frontmatter"])
    self.assertEqual(stale, [])

  def test_empty_type_fails(self) -> None:
    errors, _ = check_bundle(self._bundle(**{"a.md": "---\ntitle: X\n---\n\n# X\n"}))
    self.assertEqual(errors, ["a.md: empty `type`"])

  def test_reserved_and_superpowers_excluded(self) -> None:
    b = self._bundle(**{
      "log.md": "# Log\n\n## 2026-09-04\n- init\n",
      "superpowers/spec.md": "# spec\n",
      "index.md": "---\ntype: Directory\n---\n",
    })
    self.assertEqual(check_bundle(b), ([], []))

  def test_stale_listed_but_not_failing(self) -> None:
    past = (date.today() - timedelta(days=1)).isoformat()
    errors, stale = check_bundle(
      self._bundle(**{"plan/roadmap.md": f"---\ntype: Plan\nstale_after: {past}\n---\n\n# Roadmap\n"})
    )
    self.assertEqual(errors, [])
    self.assertEqual(stale, [f"plan/roadmap.md: stale since {past}"])

  def test_bad_stale_after_fails(self) -> None:
    errors, stale = check_bundle(self._bundle(**{"a.md": "---\ntype: Plan\nstale_after: not-a-date\n---\n\n# A\n"}))
    self.assertEqual(errors, ["a.md: bad `stale_after` (want ISO date)"])
    self.assertEqual(stale, [])
