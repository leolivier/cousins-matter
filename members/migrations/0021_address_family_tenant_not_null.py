import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
  """Make the tenant columns non-nullable, now that 0020 has backfilled them."""

  dependencies = [
    ("members", "0020_backfill_address_family_tenant"),
  ]

  operations = [
    migrations.AlterField(
      model_name="address",
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
