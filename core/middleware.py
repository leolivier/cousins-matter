"""
Custom middleware that extends LoginRequiredMiddleware to exempt OAuth URLs.
"""

import logging

from django.conf import settings
from django.contrib.auth.middleware import LoginRequiredMiddleware as BaseLoginRequiredMiddleware
from django.http import HttpRequest

logger = logging.getLogger(__name__)


# URLs that should be accessible without authentication
exempted_url_roots = getattr(settings, "LOGIN_REQUIRED_IGNORE_PATHS", [])


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

    logger.debug("  -> Not exempted, calling parent")
    # Call the parent's process_view for all other URLs
    return super().process_view(request, view_func, view_args, view_kwargs)
