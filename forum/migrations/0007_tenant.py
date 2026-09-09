import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_default_tenant(apps, schema_editor):
  Tenant = apps.get_model("tenants", "Tenant")
  Message = apps.get_model("forum", "Message")
  Post = apps.get_model("forum", "Post")
  Comment = apps.get_model("forum", "Comment")
  db = schema_editor.connection.alias
  default = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)
  # Legacy forum content lands on the default tenant.
  Message.objects.using(db).filter(tenant__isnull=True).update(tenant=default)
  Post.objects.using(db).filter(tenant__isnull=True).update(tenant=default)
  Comment.objects.using(db).filter(tenant__isnull=True).update(tenant=default)


def unassign_tenant(apps, schema_editor):
  Message = apps.get_model("forum", "Message")
  Post = apps.get_model("forum", "Post")
  Comment = apps.get_model("forum", "Comment")
  db = schema_editor.connection.alias
  Message.objects.using(db).update(tenant=None)
  Post.objects.using(db).update(tenant=None)
  Comment.objects.using(db).update(tenant=None)


class Migration(migrations.Migration):
  dependencies = [
    ("forum", "0006_alter_message_content"),
    ("tenants", "0002_seed_tenants"),
    migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    migrations.RemoveIndex(
      model_name="message",
      name="forum_messa_post_id_9ecfe0_idx",
    ),
    migrations.RemoveIndex(
      model_name="post",
      name="forum_post_title_46fb82_idx",
    ),
    migrations.RemoveIndex(
      model_name="comment",
      name="forum_comme_message_e8c1a7_idx",
    ),
    migrations.AddField(
      model_name="message",
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
      model_name="post",
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
      model_name="comment",
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
      model_name="message",
      index=models.Index(fields=["tenant", "post", "author"], name="forum_messa_tenant_4a2c19_idx"),
    ),
    migrations.AddIndex(
      model_name="post",
      index=models.Index(fields=["tenant", "title"], name="forum_post_tenant_b7d3e2_idx"),
    ),
    migrations.AddIndex(
      model_name="comment",
      index=models.Index(fields=["tenant", "message", "author"], name="forum_comme_tenant_c1f8a5_idx"),
    ),
    migrations.AlterField(
      model_name="message",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.AlterField(
      model_name="post",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
    migrations.AlterField(
      model_name="comment",
      name="tenant",
      field=models.ForeignKey(
        editable=False,
        on_delete=django.db.models.deletion.CASCADE,
        related_name="+",
        to="tenants.tenant",
      ),
    ),
  ]
