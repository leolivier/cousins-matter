"""Check OKF v0.2 conformance of a documentation bundle (default: docs/).

Every non-reserved ``.md`` file must have a YAML frontmatter with a non-empty
``type``. ``log.md`` and ``docs/superpowers/`` are excluded. Files whose
``stale_after`` date has passed are listed as warnings (not errors).
"""

import re
from datetime import date
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

RESERVED = {"log.md"}
EXCLUDED_DIRS = {"superpowers"}
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def frontmatter(text: str) -> str | None:
  m = FM_RE.match(text)
  return m.group(1) if m else None


def field(fm: str, name: str) -> str | None:
  m = re.search(rf"^{name}:\s*(.+)$", fm, re.MULTILINE)
  return m.group(1).strip() if m else None


def check_bundle(bundle: Path) -> tuple[list[str], list[str]]:
  errors: list[str] = []
  stale: list[str] = []
  for md in sorted(bundle.rglob("*.md")):
    rel = md.relative_to(bundle)
    if md.name in RESERVED or rel.parts[0] in EXCLUDED_DIRS:
      continue
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if fm is None:
      errors.append(f"{rel}: missing frontmatter")
      continue
    if not field(fm, "type"):
      errors.append(f"{rel}: empty `type`")
    sa = field(fm, "stale_after")
    if sa:
      try:
        if date.fromisoformat(sa[:10]) < date.today():
          stale.append(f"{rel}: stale since {sa[:10]}")
      except ValueError:
        errors.append(f"{rel}: bad `stale_after` (want ISO date)")
  return errors, stale


class Command(BaseCommand):
  help = "Check OKF v0.2 conformance of the docs/ bundle"

  def add_arguments(self, parser: Any) -> None:
    parser.add_argument("bundle", nargs="?", default="docs", type=str)

  def handle(self, *args: str, **options: Any) -> None:
    bundle = Path(str(options["bundle"]))
    if not bundle.is_dir():
      raise CommandError(f"bundle not found: {bundle}")
    errors, stale = check_bundle(bundle)
    for e in errors:
      self.stdout.write(self.style.ERROR(f"ERROR {e}"))
    for s in stale:
      self.stdout.write(self.style.WARNING(f"STALE  {s}"))
    if errors:
      raise SystemExit(1)
