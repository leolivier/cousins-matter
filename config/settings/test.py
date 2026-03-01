from .base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False

SECRET_KEY = env.str("SECRET_KEY", "dummy-secret-key-for-devtests")
SECRET_KEY_FALLBACKS = []

WHITENOISE_MANIFEST_STRICT = True

# Email properties
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Additional test middleware
# MIDDLEWARE.append("core.htmlvalidator.HtmlValidatorMiddleware")

# Database
DATABASES["default"]["TEST"] = {"NAME": "test_cousinsmatter"}
DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="localhost")

CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = [
  (
    env.str("REDIS_HOST", default="localhost"),
    env.int("REDIS_PORT", default=6379),
  )
]

# Django Q2 settings for tests
Q_CLUSTER["sync"] = True
