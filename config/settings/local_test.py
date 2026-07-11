from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False
WHITENOISE_MANIFEST_STRICT = True
# Email in memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# allauth ships a default "login: 30/m/ip" rate limit. The UI suite performs
# ~190 logins from localhost, which trips it (HTTP 429) and makes tests flaky
# in CI. Disable allauth rate limiting entirely in tests.
ACCOUNT_RATE_LIMITS = False

# Additional test middleware
# MIDDLEWARE.append("core.htmlvalidator.HtmlValidatorMiddleware")

# Database
DATABASES["default"]["TEST"] = {
  "NAME": "test_cousinsmatter",
  "MIRROR": None,
  "CHARSET": None,
}
DATABASES["default"]["OPTIONS"].pop("pool", None)
