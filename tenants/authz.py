"""Tenant-aware authorization helpers.

These replace the project's previous binary ``is_superuser`` "site admin"
model with platform admins (cross-tenant, ``is_superuser``) and per-tenant
admins (``Member.role == "admin"``).
"""


def is_platform_admin(user) -> bool:
  """True for the cross-tenant platform superusers."""
  return bool(user and user.is_authenticated and user.is_superuser)


def is_tenant_admin(user, tenant=None) -> bool:
  """Whether ``user`` may administer ``tenant`` (default: the current tenant).

  * Platform superusers can administer every tenant.
  * A member whose ``role`` is ``"admin"`` administers their own tenant. When
    ``tenant`` is given, it must be the user's tenant; when omitted, the check
    trusts that the request is already scoped to the user's tenant (the
    middleware guarantees this for non-superusers).
  """
  if not user or not getattr(user, "is_authenticated", False):
    return False
  if user.is_superuser:
    return True
  if getattr(user, "role", "member") != "admin":
    return False
  if tenant is None:
    return True
  return user.tenant_id == getattr(tenant, "pk", tenant)


def tenant_admins(tenant):
  """Active tenant admins of ``tenant`` (unscoped queryset).

  The replacement for the old "find the first superuser" lookups used in
  contact forms, about pages, notification emails, etc. Callers should fall
  back to platform superusers when this is empty.
  """
  from members.models import Member

  return Member.unscoped.filter(tenant=tenant, role=Member.Role.ADMIN, is_active=True)


def admin_or_superusers(tenant) -> list:
  """Tenant admins of ``tenant`` (or all platform superusers as fallback).

  Returns a list of Members suitable as email recipients / "the admin".
  """
  admins = list(tenant_admins(tenant))
  if admins:
    return admins
  from members.models import Member

  return list(Member.unscoped.filter(is_superuser=True, is_active=True))
