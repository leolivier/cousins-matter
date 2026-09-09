import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  FlatPage = apps.get_model("pages", "FlatPage")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy pages land on the default tenant.
  FlatPage.objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  FlatPage = apps.get_model("pages", "FlatPage")
  db = schema_editor.connection.alias
  FlatPage.objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("pages", "0003_migrate_page_names"),
    ("tenants", "0002_seed_tenants"),
  ]

  operations = [
    migrations.AddField(
      model_name="flatpage",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        null=True,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.RunPython(assign_default_tenant, reverse_code=unassign_tenant),
    # The url lives on the global django_flatpage (MTI parent): its global
    # unique must go so two tenants can each own "/home/authenticated/".
    # Per-tenant uniqueness is enforced by the scoped PageForm (url column
    # on the parent table has no tenant sibling for a DB constraint).
    # ponytail: form-level per-tenant uniqueness; move url to the child
    # table (data migration) if DB-level enforcement becomes a need.
    # Reverse assumes single-tenant data: re-adding the constraint fails
    # once duplicate URLs exist.
    migrations.RunSQL(
      sql="ALTER TABLE django_flatpage DROP CONSTRAINT IF EXISTS django_flatpage_url_key",  # nosec B608
      reverse_sql="ALTER TABLE django_flatpage ADD CONSTRAINT django_flatpage_url_key UNIQUE (url)",  # nosec B608
    ),
    migrations.AlterField(
      model_name="flatpage",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
  ]
