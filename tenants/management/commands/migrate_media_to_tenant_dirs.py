"""Move every protected media file under its tenant folder and rewrite DB names.

With ``MULTI_TENANT_ENABLED`` on, upload paths are prefixed with the tenant
slug (see ``tenants/storage.py``). Files uploaded before that change keep their
old names, so this command moves them and updates the DB columns. Idempotent:
a name already prefixed with its tenant slug is left untouched.
"""

import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from classified_ads.models import AdPhoto
from galleries.models import Photo
from members.models import Member
from tenants.storage import move_file
from troves.models import Trove

# (model, file field names). The member mini avatar has no DB column and is handled separately.
TARGETS = (
  (Photo, ("image", "thumbnail")),
  (Member, ("avatar",)),
  (AdPhoto, ("image", "thumbnail")),
  (Trove, ("picture", "thumbnail", "file")),
)


def prefixed(name: str, slug: str) -> str:
  """New storage name: <slug>/<old name>, unless already prefixed."""
  return name if name.split("/", 1)[0] == slug else f"{slug}/{name}"


class Command(BaseCommand):
  help = "Move protected media under <tenant slug>/ and rewrite DB file names (multi-tenant only)."

  def add_arguments(self, parser):
    parser.add_argument("--dry-run", action="store_true", help="Only report what would move.")

  def handle(self, *args, **options):
    if not settings.MULTI_TENANT_ENABLED:
      self.stdout.write("MULTI_TENANT_ENABLED is off — nothing to migrate.")
      return
    dry_run = options["dry_run"]
    stats = {"moved": 0, "already": 0, "missing": 0, "errors": 0}
    for model, field_names in TARGETS:
      for obj in model.unscoped.select_related("tenant").iterator():
        self._migrate_object(obj, field_names, dry_run, stats)
    self.stdout.write(
      f"{'would move' if dry_run else 'moved'} {stats['moved']} file(s); "
      f"{stats['already']} object(s) already in place; {stats['missing']} missing; {stats['errors']} error(s)"
    )
    if stats["errors"]:
      raise CommandError(f"{stats['errors']} file(s) could not be moved; see warnings above.")

  def _migrate_object(self, obj, field_names, dry_run, stats):  # noqa: C901
    slug = obj.tenant.slug
    planned = {}
    for field_name in field_names:
      file = getattr(obj, field_name)
      old = file.name if file else ""
      if not old:
        continue
      new = prefixed(old, slug)
      if new != old:
        planned[field_name] = (old, new)

    # dedupe image == thumbnail (small images: the thumbnail column stores the image name)
    moves = list(dict.fromkeys(planned.values()))
    if isinstance(obj, Member) and obj.avatar:
      old_avatar = obj.avatar.name
      new_avatar = planned.get("avatar", (old_avatar, old_avatar))[1]
      old_mini = os.path.join(os.path.dirname(old_avatar), "mini_" + os.path.basename(old_avatar))
      new_mini = os.path.join(os.path.dirname(new_avatar), "mini_" + os.path.basename(new_avatar))
      if old_mini != new_mini:
        moves.append((old_mini, new_mini))

    if not moves:
      stats["already"] += 1
      return

    if dry_run:
      for old, new in moves:
        if default_storage.exists(old):
          self.stdout.write(f"would move {old} -> {new}")
          stats["moved"] += 1
        else:
          self.stdout.write(f"missing: {old}")
          stats["missing"] += 1
      return

    moved = set()
    for old, new in moves:
      if not default_storage.exists(old):
        self.stderr.write(self.style.WARNING(f"missing: {old}"))
        stats["missing"] += 1
        continue
      if move_file(default_storage, old, new):
        moved.add((old, new))
        stats["moved"] += 1
      else:
        stats["errors"] += 1

    # one UPDATE per row: no save(), so no thumbnail regeneration and no signals
    updates = {field: new for field, (old, new) in planned.items() if (old, new) in moved}
    if updates:
      type(obj).unscoped.filter(pk=obj.pk).update(**updates)
