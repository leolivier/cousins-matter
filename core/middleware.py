"""
Custom middleware that extends LoginRequiredMiddleware to exempt OAuth URLs.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.middleware import LoginRequiredMiddleware as BaseLoginRequiredMiddleware
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# URLs that should be accessible without authentication
exempted_url_roots = getattr(settings, "LOGIN_REQUIRED_IGNORE_PATHS", [])

# Paths a member without privacy consent may still reach (profile shows the consent form, logout lets them leave)
CONSENT_EXEMPT_PATHS = (
  "/members/profile/",
  "/members/logout/",
  "/accounts/logout/",
  "/protected_media/",
  "/media/",
)


class LoginRequiredMiddleware(BaseLoginRequiredMiddleware):
  """
  Custom LoginRequiredMiddleware that exempts OAuth callback URLs.
  This is needed because OAuth callbacks need to be accessible without being logged in.
  """

  def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
    # Exempt OAuth-related URLs
    path = request.path_info
    logger.debug(f"LoginRequiredMiddleware checking path: {path}")
    for root in exempted_url_roots:
      if path.startswith(root):
        logger.debug(f"  -> Exempted by root: {root}")
        # Allow allauth URLs (login, signup, OAuth callbacks, etc.)
        return None

    # GDPR gate: a member who has not consented to the privacy policy can only reach their profile
    # (no extra DB query: request.user is already loaded by AuthenticationMiddleware)
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and not user.privacy_consent and not path.startswith(CONSENT_EXEMPT_PATHS):
      messages.warning(request, _("You must accept the privacy policy to use this site."))
      return redirect("members:profile")

    logger.debug("  -> Not exempted, calling parent")
    # Call the parent's process_view for all other URLs
    return super().process_view(request, view_func, view_args, view_kwargs)
