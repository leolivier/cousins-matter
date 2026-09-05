"""Forms for the multi-tenant product feature (family signup & management)."""

from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _


from .models import Tenant

# Slugs a family may never take (they collide with the seeded/special tenants
# and would break slug-based routing).
RESERVED_TENANT_SLUGS = frozenset({
  settings.DEFAULT_TENANT_SLUG,
  settings.SYSTEM_TENANT_SLUG,
  "admin",
  "admins",
  "manage",
  "settings",
  "signup",
})


def uniquify_tenant_slug(name: str) -> str:
  """Build a free tenant slug from ``name``: ``slugify(name)[:63]`` then -2, -3…

  Raises ``forms.ValidationError`` when no free slug can be found (bounded at
  100 attempts) or when the name yields an empty slug.
  """
  base = slugify(name)[:63]
  if not base:
    raise forms.ValidationError(_("This family name cannot be turned into a valid identifier."))
  if base in RESERVED_TENANT_SLUGS:
    raise forms.ValidationError(_("This family name is reserved, please choose another one."))
  slug, counter = base, 1
  while Tenant.objects.filter(slug=slug).exists() and counter < 100:
    counter += 1
    suffix = f"-{counter}"
    slug = base[: 63 - len(suffix)] + suffix
  if Tenant.objects.filter(slug=slug).exists():
    raise forms.ValidationError(_("Too many families already use this name, please choose another one."))
  return slug


class TenantCreationForm(forms.Form):
  """Create a new family (tenant). The slug is derived from the name."""

  name = forms.CharField(label=_("Family name"), max_length=200)

  def clean_name(self):
    name = self.cleaned_data["name"].strip()
    if not name:
      raise forms.ValidationError(_("This field is required."))
    return name

  def clean(self):
    cleaned = super().clean()
    if "name" in cleaned:
      # compute the slug here so errors surface on the form, not at view time
      cleaned["slug"] = uniquify_tenant_slug(cleaned["name"])
    return cleaned
