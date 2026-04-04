from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False
WHITENOISE_MANIFEST_STRICT = True
# Email in memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# Database
DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="postgres")
DATABASES["default"]["OPTIONS"].pop("pool", None)
DATABASES["default"]["TEST"] = {
  "NAME": "test_cousinsmatter",
  "MIRROR": None,
  "CHARSET": None,
}

CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = [
  (
    env.str("REDIS_HOST", default="redis"),
    env.int("REDIS_PORT", default=6379),
  )
]

# Django Q2 settings for tests
Q_CLUSTER["sync"] = True
