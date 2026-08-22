from django.contrib.auth.base_user import BaseUserManager
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _


class MemberManager(BaseUserManager):
  """
  Member model manager where first_name, last_name are mandatory.

  Tenant-aware: ``get_queryset`` filters by the current tenant when one is
  active, and is left unfiltered otherwise (anonymous request, management
  command, platform superuser) so authentication lookups and createsuperuser
  keep working. Use ``Member.unscoped`` for explicit cross-tenant access.
  """

  def get_queryset(self):
    from tenants.scoping import get_current_tenant

    qs = super().get_queryset()
    tenant = get_current_tenant()
    return qs.filter(tenant=tenant) if tenant is not None else qs

  def _resolve_tenant(self, extra_fields):
    """Ensure a tenant is present: explicit > current request > default."""
    if extra_fields.get("tenant") is not None:
      return
    from tenants.models import Tenant
    from tenants.scoping import get_current_tenant

    extra_fields["tenant"] = get_current_tenant() or Tenant.get_default()

  def create_member(self, username: str, email: str, password: str, first_name: str, last_name: str, **extra_fields):
    """
    Create and save a user with the given username, email, password, first_name and last_name.
    """
    if not username:
      raise ValueError(_("The username must be set"))

    extra_fields.setdefault("is_active", False)
    self._resolve_tenant(extra_fields)

    if email:
      email = self.normalize_email(email)
    user = self.model(
      username=username,
      email=email,
      first_name=first_name,
      last_name=last_name,
      **extra_fields,
    )
    user.set_password(password)
    user.save()
    return user

  async def acreate_member(self, username, email, password, first_name, last_name, **extra_fields):
    """
    Async version of create_member
    """
    if not username:
      raise ValueError(_("The username must be set"))

    extra_fields.setdefault("is_active", False)
    self._resolve_tenant(extra_fields)

    if email:
      email = self.normalize_email(email)
    user = self.model(
      username=username,
      email=email,
      first_name=first_name,
      last_name=last_name,
      **extra_fields,
    )
    user.set_password(password)
    await user.asave()
    return user

  def create_superuser(self, username: str, email: str, password: str, first_name: str, last_name: str, **extra_fields):
    """
    Create and save a SuperUser with the given email and password.

    A superuser is a cross-tenant platform admin living on the system tenant.
    """
    extra_fields.setdefault("is_staff", True)
    extra_fields.setdefault("is_superuser", True)
    extra_fields.setdefault("is_active", True)
    extra_fields.setdefault("role", "admin")
    from tenants.models import Tenant

    extra_fields.setdefault("tenant", Tenant.get_system())

    if extra_fields.get("is_staff") is not True:
      raise ValueError(_("Superuser must have is_staff=True."))
    if extra_fields.get("is_superuser") is not True:
      raise ValueError(_("Superuser must have is_superuser=True."))
    return self.create_member(username, email, password, first_name, last_name, **extra_fields)

  def alive(self):
    return self.get_queryset().filter(is_dead=False)

  def dead(self):
    return self.get_queryset().filter(is_dead=True)

  def fuzzy_search(self, query: str, similarity_threshold: float = 0.2) -> QuerySet:
    return (
      self
      .get_queryset()
      .annotate(
        complete_name=Concat("first_name", Value(" "), "last_name"), similarity=TrigramSimilarity("complete_name", query)
      )
      .filter(similarity__gt=similarity_threshold)
      .order_by("-similarity")
      .distinct()
    )

  # for m in list(members):
  #   print(m.full_name, "similarity", m.similarity)
