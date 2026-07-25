import socket

from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", True)

TESTING = False

# debug_toolbar is a dev-group dependency; the Dockerfile installs deps with
# `uv sync --no-group dev`, so the package is absent from the container and
# importing it crashes the qcluster (and any docker service) on startup.
# Default off here, matching docker_test.py; enable via DEBUG_TOOLBAR=true only
# if the package is installed in the image.
DEBUG_TOOLBAR = env.bool("DEBUG_TOOLBAR", default=False)
DEBUG_HTMX = env.bool("DEBUG_HTMX", default=DEBUG)


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
    pass  # noqa: F401  # nosec B110

DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="postgres")
# Keep the robust dict-format config from base.py; only retarget the address.
# A plain (host, port) tuple would drop all connection options (socket_timeout,
# socket_keepalive, health_check_interval) and leave Channels vulnerable to
# "Timeout reading" errors when pooled connections go dead.
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]["address"] = (
  f"redis://{env.str('REDIS_HOST', default='redis')}:{env.int('REDIS_PORT', default=6379)}"
)

CRISPY_FAIL_SILENTLY = False
