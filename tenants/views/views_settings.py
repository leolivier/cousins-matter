"""Family settings form + view (tenant admin edits branding + behavior keys).

Only keys from ``TENANT_SETTINGS_SPEC`` are editable. ``save()`` persists ONLY
the deltas vs the global defaults so a later global flip still propagates to
families that never overrode a key.
"""

from django import forms
from django.conf import settings as django_settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import generic

from . import multi_tenant_required
from tenants.settings_overrides import TENANT_SETTINGS_SPEC

# Keys that must stay boolean in the form
_BOOL_KEYS = {"dark_mode", "allow_members_to_create_members", "allow_members_to_invite_members"}
# Keys accepting an empty value (stored as None)
_NULLABLE_KEYS = {"site_copyright", "site_footer", "family_chart_root_person_id"}
_PDF_SIZES = ("A4", "letter")


class TenantSettingsForm(forms.Form):
  """Edit a family's overrides; generated from TENANT_SETTINGS_SPEC."""

  site_name = forms.CharField(label=_("Family site name"), max_length=200, required=False)
  site_logo = forms.CharField(label=_("Site logo (static/media path)"), max_length=500, required=False)
  site_copyright = forms.CharField(label=_("Copyright line"), max_length=500, required=False)
  site_footer = forms.CharField(label=_("Footer text"), max_length=500, required=False)
  pdf_size = forms.ChoiceField(label=_("PDF page size"), choices=[(s, s) for s in _PDF_SIZES])
  dark_mode = forms.BooleanField(label=_("Dark mode by default"), required=False)
  language_code = forms.ChoiceField(label=_("Language"), choices=getattr(django_settings, "LANGUAGES", []))
  time_zone = forms.CharField(label=_("Time zone (IANA, e.g. Europe/Paris)"), max_length=64)
  birthday_days = forms.IntegerField(label=_("Birthday lookahead (days)"), min_value=-365, max_value=365)
  allow_members_to_create_members = forms.BooleanField(label=_("Members can create members"), required=False)
  allow_members_to_invite_members = forms.BooleanField(label=_("Members can invite members"), required=False)
  family_chart_root_person_id = forms.IntegerField(
    label=_("Genealogy chart root member id (optional)"), required=False, min_value=1
  )

  def __init__(self, *args, tenant=None, **kwargs):
    super().__init__(*args, **kwargs)
    self.tenant = tenant
    # current effective values as initial (override if set, else global)
    for key in TENANT_SETTINGS_SPEC:
      if key in self.fields:
        self.fields[key].initial = _setting_for(key, tenant)

  def clean_family_chart_root_person_id(self):
    pid = self.cleaned_data.get("family_chart_root_person_id")
    if pid is None:
      return None
    from members.models import Member

    member = Member.unscoped.filter(pk=pid, tenant=self.tenant).first()
    if member is None:
      raise forms.ValidationError(_("This member does not belong to your family."))
    return pid

  def clean_time_zone(self):
    tz = self.cleaned_data["time_zone"]
    try:
      from zoneinfo import ZoneInfo

      ZoneInfo(tz)
    except Exception:
      raise forms.ValidationError(_("Unknown time zone."))
    return tz

  def save(self):
    """Persist only the deltas vs global defaults into TenantSettings.overrides."""
    from tenants.models import TenantSettings

    row, _created = TenantSettings.objects.get_or_create(tenant=self.tenant)
    overrides = dict(row.overrides or {})
    for key, setting_name in TENANT_SETTINGS_SPEC.items():
      if key not in self.cleaned_data:
        continue
      value = self.cleaned_data.get(key)
      global_value = getattr(django_settings, setting_name, None)
      # normalize booleans/empty: store only when it truly differs from global
      if key in _BOOL_KEYS:
        differs = bool(value) != bool(global_value)
      elif value in (None, ""):
        differs = global_value not in (None, "")
        value = None
      else:
        differs = value != global_value
      if differs:
        overrides[key] = value
      else:
        overrides.pop(key, None)
    row.overrides = overrides
    row.save()

    # invalidate caches so changes apply immediately
    from core.templatetags.cm_tags import clear_flags_cache
    from tenants.settings_overrides import clear_tenant_settings_cache

    clear_flags_cache()
    clear_tenant_settings_cache()
    if "family_chart_root_person_id" in self.changed_data:
      from genealogy.utils import clear_genealogy_caches

      clear_genealogy_caches()
    return row


def _setting_for(key, tenant):
  """Effective value of ``key`` for ``tenant`` (override or global)."""
  from tenants.models import tenant_settings_overrides
  from tenants.settings_overrides import TENANT_SETTINGS_SPEC

  override = tenant_settings_overrides(tenant).get(key)
  if override is not None:
    return override
  return getattr(django_settings, TENANT_SETTINGS_SPEC[key], None)


class TenantSettingsUpdateView(generic.View):
  """A family admin edits their own family's settings.

  A platform superuser may pass ``?tenant=<slug>`` to edit any family; for
  anyone else the parameter is ignored (no IDOR: they only ever touch their
  own tenant).
  """

  template_name = "tenants/tenant_settings.html"
  title = _("Family settings")

  def _get_tenant(self, request):
    if request.user.is_superuser:
      slug = request.GET.get("tenant") or request.POST.get("tenant")
      if slug:
        from tenants.models import Tenant

        return get_object_or_404(Tenant.objects, slug=slug)
    return request.user.tenant

  def dispatch(self, request, *args, **kwargs):
    multi_tenant_required()
    if not (request.user.is_authenticated and (request.user.is_superuser or request.user.is_tenant_admin)):
      raise PermissionDenied(_("Only family administrators can edit family settings."))
    return super().dispatch(request, *args, **kwargs)

  def get(self, request):
    tenant = self._get_tenant(request)
    form = TenantSettingsForm(tenant=tenant)
    return render(request, self.template_name, {"form": form, "tenant": tenant, "title": self.title})

  def post(self, request):
    tenant = self._get_tenant(request)
    form = TenantSettingsForm(request.POST, tenant=tenant)
    if form.is_valid():
      form.save()
      messages.success(request, _("Family settings updated."))
      return redirect("tenants:settings")
    return render(request, self.template_name, {"form": form, "tenant": tenant, "title": self.title})
