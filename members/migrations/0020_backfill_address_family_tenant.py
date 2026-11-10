from django.db import migrations


def backfill_tenants(apps, schema_editor):
  """Give every Address/Family the tenant of the members that reference it.

  Rows shared by members of several tenants (possible through the old
  unscoped CSV import) are duplicated: the original keeps the first tenant,
  each extra tenant gets its own copy and its members are repointed.
  Unreferenced rows land on the default tenant.
  """
  from django.conf import settings

  Address = apps.get_model("members", "Address")
  Family = apps.get_model("members", "Family")
  Member = apps.get_model("members", "Member")
  Tenant = apps.get_model("tenants", "Tenant")
  db = schema_editor.connection.alias
  default_tenant = Tenant.objects.using(db).get(slug=settings.DEFAULT_TENANT_SLUG)

  def assign(model, member_field):
    for obj in model.objects.using(db).all():
      tenant_ids = list(
        Member.objects.using(db)
        .filter(**{f"{member_field}_id": obj.pk})
        .exclude(tenant_id=None)
        .values_list("tenant_id", flat=True)
        .distinct()
      )
      if not tenant_ids:
        model.objects.using(db).filter(pk=obj.pk).update(tenant_id=default_tenant.pk)
        continue
      model.objects.using(db).filter(pk=obj.pk).update(tenant_id=tenant_ids[0])
      for extra_tenant in tenant_ids[1:]:
        copy = model.objects.using(db).get(pk=obj.pk)
        copy.pk = None
        copy.tenant_id = extra_tenant
        copy.save(using=db)
        Member.objects.using(db).filter(
          **{f"{member_field}_id": obj.pk}, tenant_id=extra_tenant
        ).update(**{f"{member_field}_id": copy.pk})

  assign(Address, "address")
  assign(Family, "family")
  # A family's parent must live on the same tenant.
  for family in Family.objects.using(db).select_related("parent"):
    if family.parent_id and family.parent.tenant_id != family.tenant_id:
      Family.objects.using(db).filter(pk=family.pk).update(parent=None)


class Migration(migrations.Migration):
  """Data-only migration: no schema change, so no ALTER blocked by triggers."""

  dependencies = [
    ("members", "0019_address_family_tenant"),
  ]

  operations = [
    migrations.RunPython(backfill_tenants, migrations.RunPython.noop),
  ]
