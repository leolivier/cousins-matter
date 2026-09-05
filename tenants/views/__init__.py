"""Views for the multi-tenant product feature.

All views here live under the /tenants/ URL prefix, which is only mounted when
``MULTI_TENANT_ENABLED`` is on (see cousinsmatter/urls.py). Each view also
calls :func:`multi_tenant_required` as defense in depth, so it stays safe even
if the URLs are ever included unconditionally.
"""

from django.conf import settings
from django.http import Http404


def multi_tenant_required():
  """Raise Http404 when the multi-tenant feature flag is off."""
  if not getattr(settings, "MULTI_TENANT_ENABLED", False):
    raise Http404("Multi-tenancy is not enabled on this deployment.")
