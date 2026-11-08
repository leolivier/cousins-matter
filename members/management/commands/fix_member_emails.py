"""Interactive fix for the records blocking migration 0018.

Re-runs the exact checks of ``members.migrations.0018`` (duplicate
case-insensitive emails across tenants, active members without email) and
asks for a decision on each offending record. Identity decisions (who keeps
an email, who manages a deactivated member) are never automatic.

Run it against the same database you migrate::

    python manage.py fix_member_emails

Answer every prompt (or skip freely), re-run until it reports
"Nothing to fix", then run ``migrate``.
"""

import django.db.models.functions.text
from django.core.management.base import BaseCommand
from django.core.validators import EmailValidator
from django.db import models

from tenants.scoping import tenant_context

EMAIL_VALIDATOR = EmailValidator()
DUPLICATE = "duplicate email"
MISSING = "active member has no email"


class Command(BaseCommand):
  help = __doc__

  def handle(self, *args, **options):
    from members.models import Member

    # Same context as the migration: cross-tenant view of every member.
    with tenant_context(None):
      problems = self.find_problems(Member)
      if not problems:
        self.stdout.write(self.style.SUCCESS("Nothing to fix: run migrate now."))
        return

      for kind, detail, members in problems:
        if kind == DUPLICATE:
          self.fix_duplicate(Member, detail, members)
        else:
          self.fix_missing_email(Member, members[0])

      remaining = self.find_problems(Member)
      if remaining:
        lines = [self.message(k, d) for k, d, _ in remaining]
        self.stdout.write(self.style.ERROR(f"{len(remaining)} problem(s) remain:\n  " + "\n  ".join(lines)))
      else:
        self.stdout.write(self.style.SUCCESS("All records fixed: run migrate now."))

  @staticmethod
  def message(kind, detail):
    return f"{kind} {detail!r}" if kind == DUPLICATE else f"{kind} (id {detail})"

  @staticmethod
  def find_problems(Member):
    """Mirror members.migrations.0018.check_email_data."""
    problems = []
    duplicates = (
      Member.objects
      .exclude(email="")
      .annotate(email_lower=django.db.models.functions.text.Lower("email"))
      .values("email_lower")
      .annotate(count=models.Count("id"))
      .filter(count__gt=1)
    )
    for row in duplicates:
      members = list(
        Member.objects.annotate(email_lower=django.db.models.functions.text.Lower("email")).filter(
          email_lower=row["email_lower"]
        )
      )
      problems.append((DUPLICATE, row["email_lower"], members))
    for member in Member.objects.filter(is_active=True, email=""):
      problems.append((MISSING, member.pk, [member]))
    return problems

  @classmethod
  def describe(cls, members):
    return "\n".join(f"  {m.pk}: {m} [{m.tenant.name}] active={m.is_active} dead={m.is_dead}" for m in members)

  def fix_duplicate(self, Member, email, members):
    self.stdout.write(self.style.WARNING(f"\n{self.message(DUPLICATE, email)}:"))
    self.stdout.write(self.describe(members))
    keeper = self.pick_member(
      "Which member id keeps the email?", members, default=next((m for m in members if m.is_active), members[0])
    )
    if not keeper.is_active:
      self.stdout.write("Warning: keeper is inactive, it cannot manage the others (pick another manager below).")
    for member in members:
      if member.pk == keeper.pk:
        continue
      self.stdout.write(f"\n  Member {member.pk} ({member}) also uses {email!r}.")
      choice = input("  [d]eactivate & manage by keeper, [e]nter another email, [s]kip: ").strip().lower()
      if choice == "d":
        self.deactivate(Member, member, prefer=[keeper])
      elif choice == "e":
        self.set_email(Member, member)
      else:
        self.stdout.write(self.style.WARNING(f"  Skipped {member.pk}."))

  def fix_missing_email(self, Member, member):
    self.stdout.write(self.style.WARNING(f"\n{self.message(MISSING, member.pk)}: {member} [{member.tenant.name}]"))
    choice = input("  [e]nter the member's email, [d]eactivate & manage by another member, [s]kip: ").strip().lower()
    if choice == "e":
      self.set_email(Member, member)
    elif choice == "d":
      self.deactivate(Member, member)
    else:
      self.stdout.write(self.style.WARNING(f"  Skipped {member.pk}."))

  def pick_member(self, prompt, members, default=None):
    default_hint = f" [default {default.pk}]" if default is not None else ""
    while True:
      answer = input(f"{prompt}{default_hint}: ").strip()
      if not answer:
        return default
      try:
        return next(m for m in members if str(m.pk) == answer)
      except StopIteration:
        self.stdout.write("Unknown id, try again.")

  def set_email(self, Member, member):
    while True:
      email = input(f"  Email for {member.pk} ({member}): ").strip()
      if not email:
        self.stdout.write("  Empty email: skipping.")
        return
      try:
        EMAIL_VALIDATOR(email)
      except Exception as e:
        self.stdout.write(f"  Invalid email ({e}), try again or leave empty to skip.")
        continue
      clash = (
        Member.objects
        .exclude(pk=member.pk)
        .annotate(email_lower=django.db.models.functions.text.Lower("email"))
        .filter(email_lower=email.lower())
      )
      if clash.exists():
        self.stdout.write(f"  Already used by {clash[0].pk} ({clash[0]}), try another one.")
        continue
      member.email = email
      member.save()
      self.stdout.write(self.style.SUCCESS(f"  {member.pk}: email set to {email!r}."))
      return

  def deactivate(self, Member, member, prefer=None):
    """Set the member inactive and assign a manager (active member with an email)."""
    candidates = list(Member.objects.exclude(pk=member.pk).filter(is_active=True).exclude(email="").order_by("pk"))
    if not candidates:
      self.stdout.write(self.style.ERROR(f"  No active member with an email to manage them, skipped {member.pk}."))
      return
    default = next((c for c in (prefer or []) if c in candidates), None)
    if default is None:
      default = next((c for c in candidates if c.tenant_id == member.tenant_id and c.role == Member.Role.ADMIN), None)
    self.stdout.write("  Manager candidates:\n" + self.describe(candidates))
    manager = self.pick_member("  Who manages them?", candidates, default=default)
    member.is_active = False
    member.member_manager = manager
    member.save()
    self.stdout.write(self.style.SUCCESS(f"  {member.pk}: deactivated, managed by {manager.pk} ({manager})."))
