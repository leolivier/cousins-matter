import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  Trove = apps.get_model("troves", "Trove")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy troves land on the default tenant.
  Trove.objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  Trove = apps.get_model("troves", "Trove")
  db = schema_editor.connection.alias
  Trove.objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("troves", "0004_alter_trove_title"),
    ("tenants", "0002_seed_tenants"),
    migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    migrations.RemoveIndex(
      model_name="trove",
      name="troves_trov_categor_900909_idx",
    ),
    migrations.AddField(
      model_name="trove",
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
    migrations.AddIndex(
      model_name="trove",
      index=models.Index(fields=["tenant", "category"], name="troves_trov_tenant_c30fb4_idx"),
    ),
    migrations.AlterField(
      model_name="trove",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
  ]
