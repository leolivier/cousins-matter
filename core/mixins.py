from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.mixins import PermissionRequiredMixin


class LoginNotRequiredMixin:
  """
  Mixin to exempt a view from the LoginRequiredMiddleware.
  """

  @classmethod
  def as_view(cls, *args, **kwargs):
    view = super().as_view(*args, **kwargs)
    return login_not_required(view)


class OnlyAdminMixin(PermissionRequiredMixin):
  """Allows platform superusers and tenant admins; denies everyone else."""
  raise_exception = True

  def has_permission(self):
    user = self.request.user
    return user.is_authenticated and (user.is_superuser or getattr(user, "is_tenant_admin", False))
