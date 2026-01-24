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
  raise_exception = True
  permission_required = "is_superuser"
