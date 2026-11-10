import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
  """Add the nullable tenant columns (schema only).

  Kept free of data changes: Django emits the FK ``CREATE INDEX`` statements
  after any ``RunPython`` in the same migration, and PostgreSQL refuses to
  create them while the backfill's deferred FK triggers are still pending.
  The backfill (0020) and the non-nullable alteration (0021) are separate
  migrations, each in its own transaction.
  """

  dependencies = [
    ("members", "0018_member_member_email_uniq_and_more"),
  ]

  operations = [
    migrations.AddField(
      model_name="address",
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
  ]
