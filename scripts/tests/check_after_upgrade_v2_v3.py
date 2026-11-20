"""Verify the v2 -> v3 upgrade.

Runs inside the v3 image (see scripts/tests/test_upgrade_v2_v3.sh): every row
seeded by seed_v2_data.py must survive and be assigned to the default tenant,
while platform superusers must land on the system tenant.
"""

from django.conf import settings

from chat.models import ChatMessage, ChatRoom
from classified_ads.models import ClassifiedAd
from forum.models import Message, Post
from galleries.models import Gallery
from genealogy.models import Person
from members.models import Member
from pages.models import FlatPage
from polls.models import Poll
from tenants.models import Tenant
from troves.models import Trove

errors: list[str] = []


def check(condition, message):
  if not condition:
    errors.append(message)


default = Tenant.objects.get(slug=settings.DEFAULT_TENANT_SLUG)
system = Tenant.objects.get(slug=settings.SYSTEM_TENANT_SLUG)

legacy = Member.unscoped.filter(username="legacy-member").first()
check(legacy is not None, "legacy member was lost")
if legacy is not None:
  check(legacy.check_password("legacy-password"), "legacy member password changed")
  check(legacy.tenant_id == default.pk, "legacy member is not on the default tenant")

admin = Member.unscoped.filter(is_superuser=True).first()
check(admin is not None, "platform superuser was lost")
if admin is not None:
  check(admin.tenant_id == system.pk, "platform superuser is not on the system tenant")

scoped_models = [
  ("gallery", Gallery),
  ("forum message", Message),
  ("forum post", Post),
  ("poll", Poll),
  ("classified ad", ClassifiedAd),
  ("trove", Trove),
  ("genealogy person", Person),
  ("chat room", ChatRoom),
  ("chat message", ChatMessage),
  ("flat page", FlatPage),
]

for label, model in scoped_models:
  rows = model.unscoped.all()
  check(rows.exists(), f"legacy {label} was lost")
  check(not rows.filter(tenant__isnull=True).exists(), f"some {label} rows have no tenant")
  check(not rows.exclude(tenant=default).exists(), f"some {label} rows are not on the default tenant")

if errors:
  raise SystemExit("post-upgrade checks failed:\n- " + "\n- ".join(errors))
print("post-upgrade checks passed")
