import json
from pathlib import Path

from django.conf import settings
from django.contrib.sites.models import Site

from .models import FlatPage

FIXTURE = Path(__file__).parent / "fixtures" / "predefined_flatpages.json"


def seed_tenant_pages(tenant):
  """Seed a freshly created tenant with its own copy of the predefined pages.

  Each family gets independent, editable home/about pages: rows are
  copies scoped to ``tenant`` (predefined/updated flags from the
  fixture). The base ``django_flatpage`` table stays global, so the
  same URL may exist once per tenant.
  """
  with open(FIXTURE) as fixture_file:
    entries = json.load(fixture_file)
  base_by_pk = {entry["pk"]: entry["fields"] for entry in entries if entry["model"] == "flatpages.flatpage"}
  site = Site.objects.get(pk=settings.SITE_ID)
  for entry in entries:
    if entry["model"] != "pages.flatpage":
      continue
    base = base_by_pk[entry["pk"]]
    child = entry["fields"]
    page = FlatPage.objects.create(
      tenant=tenant,
      url=base["url"],
      title=base["title"],
      content=base["content"],
      enable_comments=base.get("enable_comments", False),
      template_name=base.get("template_name", ""),
      registration_required=base.get("registration_required", False),
      predefined=child.get("predefined", True),
      updated=child.get("updated", False),
    )
    page.sites.set([site])
  return FlatPage.unscoped.filter(tenant=tenant).count()
