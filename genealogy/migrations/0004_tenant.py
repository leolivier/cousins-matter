import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  Person = apps.get_model("genealogy", "Person")
  Family = apps.get_model("genealogy", "Family")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy people/families land on the default tenant.
  Person.objects.using(db).filter(tenant__isnull=True).update(tenant=default)
  Family.objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  Person = apps.get_model("genealogy", "Person")
  Family = apps.get_model("genealogy", "Family")
  db = schema_editor.connection.alias
  Person.objects.using(db).update(tenant=None)
  Family.objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("genealogy", "0003_alter_person_uid"),
    ("tenants", "0002_seed_tenants"),
  ]

  operations = [
    migrations.AddField(
      model_name="person",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        null=True,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.AddField(
      model_name="family",
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
      model_name="person",
      index=models.Index(fields=["tenant", "last_name"], name="person_tenant_last_name_idx"),
    ),
    migrations.AddIndex(
      model_name="person",
      index=models.Index(fields=["tenant", "birth_date"], name="person_tenant_birth_date_idx"),
    ),
    # The per-tenant constraint goes live before the global unique drops, so
    # GEDCOM ids stay protected throughout the switch.
    migrations.AddConstraint(
      model_name="person",
      constraint=models.UniqueConstraint(
        fields=("tenant", "gedcom_id"), name="person_tenant_gedcom_id_uniq"
      ),
    ),
    migrations.AlterField(
      model_name="person",
      name="gedcom_id",
      field=models.CharField(blank=True, max_length=50, null=True, verbose_name="GEDCOM ID"),
    ),
    migrations.RemoveIndex(
      model_name="person",
      name="genealogy_p_last_na_5cd12f_idx",
    ),
    migrations.RemoveIndex(
      model_name="person",
      name="genealogy_p_birth_d_c5547a_idx",
    ),
    migrations.AlterField(
      model_name="person",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.AlterField(
      model_name="family",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
  ]
