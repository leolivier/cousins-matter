"""Tenant-aware replacement for django.contrib.flatpages' fallback middleware.

The stock ``FlatpageFallbackMiddleware`` resolves 404s against the
global ``django_flatpage`` table — a cross-tenant leak. This version
routes through the scoped ``pages.views.flatpage`` and serves the
tenant's own page or re-raises the original 404.
"""

from django.http import Http404

from .views import flatpage


class TenantFlatpageFallbackMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    response = self.get_response(request)
    if response.status_code != 404:
      return response
    try:
      return flatpage(request, request.path)
    except Http404:
      return response
