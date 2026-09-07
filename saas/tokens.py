"""Signed, stateless validation links for tenant requests.

Reuses the members ``TokenManager`` HMAC machinery with the SaaS max-age;
the link carries ``"<pk>:<email>"`` so a request cannot be swapped for
another one.
"""

from base64 import urlsafe_b64decode, urlsafe_b64encode

from django.conf import settings
from django.urls import reverse

from members.registration_link_manager import TokenManager

from .models import TenantRequest


class TenantRequestTokenManager(TokenManager):
  def __init__(self) -> None:
    self.max_age = settings.SAAS_TENANT_REQUEST_MAX_AGE

  @staticmethod
  def _payload(tenant_request: TenantRequest) -> str:
    return f"{tenant_request.pk}:{tenant_request.email}"

  def generate_link(self, request, tenant_request: TenantRequest) -> str:
    payload = self._payload(tenant_request)
    token = self.make_token(payload)
    encoded = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
    return request.build_absolute_uri(reverse("saas:validate", args=(encoded, token)))

  def decrypt_link(self, encoded, token) -> TenantRequest | None:
    """Return the ``TenantRequest`` for a valid, unexpired link, else ``None``."""
    try:
      payload = urlsafe_b64decode(encoded).decode("utf-8")
    except Exception:  # malformed base64
      return None
    if not payload or not self.check_token(payload, token):
      return None
    pk, _, email = payload.partition(":")
    if not pk.isdigit():
      return None
    tenant_request = TenantRequest.objects.filter(pk=int(pk)).first()
    if tenant_request is None or tenant_request.email != email:
      return None
    return tenant_request
