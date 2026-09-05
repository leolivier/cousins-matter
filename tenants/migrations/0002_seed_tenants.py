"""Seed the default and system tenants.

The default tenant is assigned when none can be resolved (legacy data,
management commands). The system tenant hosts the cross-tenant platform
superusers. Both are created idempotently from the configured slugs.
"""

from django.conf import settings
from django.db import migrations


def seed_tenants(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  db_alias = schema_editor.connection.alias
  Tenant.objects.using(db_alias).get_or_create(
    slug=settings.DEFAULT_TENANT_SLUG,
    defaults={"name": "Default", "is_active": True},
  )
  Tenant.objects.using(db_alias).get_or_create(
    slug=settings.SYSTEM_TENANT_SLUG,
    defaults={"name": "System", "is_active": True},
  )


def remove_seed(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  db_alias = schema_editor.connection.alias
  Tenant.objects.using(db_alias).filter(
    slug__in=[settings.DEFAULT_TENANT_SLUG, settings.SYSTEM_TENANT_SLUG]
  ).delete()


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0001_initial"),
  ]

  operations = [
    migrations.RunPython(seed_tenants, reverse_code=remove_seed),
  ]
