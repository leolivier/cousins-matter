"""Server-side verification of the Cloudflare Turnstile widget.

No-op success while ``TURNSTILE_ENABLED`` is off (dev/test, no network);
when on, fails closed on any error so the signup cannot be bypassed by a
network hiccup.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(request) -> bool:
  if not settings.TURNSTILE_ENABLED:
    return True
  token = request.POST.get("cf-turnstile-response", "")
  if not token:
    return False
  try:
    response = requests.post(
      VERIFY_URL,
      data={
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
        "remoteip": request.META.get("REMOTE_ADDR", ""),
      },
      timeout=5,
    )
    return bool(response.json().get("success", False))
  except Exception:
    logger.warning("Turnstile verification failed (network error or bad response).")
    return False
