import socket
from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", True)

TESTING = False

DEBUG_TOOLBAR = env.bool("DEBUG_TOOLBAR", default=True)
DEBUG_HTMX = env.bool("DEBUG_HTMX", default=DEBUG)

# Support for ngrok
ALLOWED_HOSTS.append(".ngrok-free.app")
CSRF_TRUSTED_ORIGINS.append("https://*.ngrok-free.app")
# To ensure Django knows it's behind an HTTPS proxy (ngrok)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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

DATABASES["default"]["USER"] = "cousinsmatter"

CRISPY_FAIL_SILENTLY = False
