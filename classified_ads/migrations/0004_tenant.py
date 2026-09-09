import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  ClassifiedAd = apps.get_model("classified_ads", "ClassifiedAd")
  AdPhoto = apps.get_model("classified_ads", "AdPhoto")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy ads/photos land on the default tenant.
  ClassifiedAd.objects.using(db).filter(tenant__isnull=True).update(tenant=default)
  AdPhoto.objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  ClassifiedAd = apps.get_model("classified_ads", "ClassifiedAd")
  AdPhoto = apps.get_model("classified_ads", "AdPhoto")
  db = schema_editor.connection.alias
  ClassifiedAd.objects.using(db).update(tenant=None)
  AdPhoto.objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("classified_ads", "0003_adphoto_thumbnail_alter_adphoto_image_and_more"),
    ("tenants", "0002_seed_tenants"),
    migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    migrations.RemoveIndex(
      model_name="classifiedad",
      name="classified__owner_i_f37fd9_idx",
    ),
    migrations.RemoveIndex(
      model_name="adphoto",
      name="classified__ad_id_8408d9_idx",
    ),
    migrations.AddField(
      model_name="classifiedad",
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
      model_name="adphoto",
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
      model_name="classifiedad",
      index=models.Index(
        fields=["tenant", "owner", "category", "subcategory"],
        name="classified_tenant_9d2f4a_idx",
      ),
    ),
    migrations.AddIndex(
      model_name="adphoto",
      index=models.Index(fields=["tenant", "ad"], name="classified_tenant_a1c7e8_idx"),
    ),
    migrations.AlterField(
      model_name="classifiedad",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.AlterField(
      model_name="adphoto",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
  ]
