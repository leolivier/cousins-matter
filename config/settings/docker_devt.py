import socket

from .base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", True)

TESTING = False

DEBUG_TOOLBAR = env.bool("DEBUG_TOOLBAR", default=True)
DEBUG_HTMX = env.bool("DEBUG_HTMX", default=DEBUG)

SECRET_KEY = env.str("SECRET_KEY", "dummy-secret-key-for-devtests")
SECRET_KEY_FALLBACKS = []

if getattr(base, "SITE_DOMAIN", None) is None:
  SITE_DOMAIN = "localhost"
  SITE_PORT = 8000

WHITENOISE_MANIFEST_STRICT = False

# Email properties
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Log levels
CM_LOG_LEVEL = env.str("CM_LOG_LEVEL", default="DEBUG")
for app in LOCAL_APPS:
  LOGGING["loggers"][app]["level"] = CM_LOG_LEVEL

# MIDDLEWARE.append('core.htmlvalidator.HtmlValidatorMiddleware')

if DEBUG_TOOLBAR:
  INSTALLED_APPS.append("debug_toolbar")
  MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
  ]
  INTERNAL_IPS = [
    "127.0.0.1",
    "::1",
  ]
  try:
    hostname, __un__, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]
  except Exception:
    pass

DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="postgres")
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = [
  (
    env.str("REDIS_HOST", default="redis"),
    env.int("REDIS_PORT", default=6379),
  )
]

CRISPY_FAIL_SILENTLY = False

# Django Q2 settings
Q_CLUSTER["sync"] = env.bool("Q_SYNC", True)  # Synchronous by default in dev for easier debugging
