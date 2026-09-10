import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Concrete polls models carrying a local tenant column after this migration.
# MTI children (EventPlanner < Poll, SingleEventAnswer < ChoiceAnswer,
# MultiEventAnswer < MultiChoiceAnswer) hold no column: the tenant lives on
# the parent table, like chat's PrivateChatRoom.
POLL_MODELS = (
  "poll",
  "question",
  "pollanswer",
  "yesnoanswer",
  "textanswer",
  "datetimeanswer",
  "choiceanswer",
  "multichoiceanswer",
)


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy polls content lands on the default tenant.
  for name in POLL_MODELS:
    apps.get_model("polls", name).objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  db = schema_editor.connection.alias
  for name in POLL_MODELS:
    apps.get_model("polls", name).objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("polls", "0004_eventplanner_multichoiceanswer_singleeventanswer_and_more"),
    ("tenants", "0002_seed_tenants"),
    migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    *[
      migrations.AddField(
        model_name=name,
        name="tenant",
        field=models.ForeignKey(
          editable=False,
          null=True,
          on_delete=django.db.models.deletion.CASCADE,
          related_name="+",
          to="tenants.tenant",
        ),
      )
      for name in POLL_MODELS
    ],
    migrations.RunPython(assign_default_tenant, reverse_code=unassign_tenant),
    *[
      migrations.AlterField(
        model_name=name,
        name="tenant",
        field=models.ForeignKey(
          editable=False,
          on_delete=django.db.models.deletion.CASCADE,
          related_name="+",
          to="tenants.tenant",
        ),
      )
      for name in POLL_MODELS
    ],
  ]
