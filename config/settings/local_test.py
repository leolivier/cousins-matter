from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False
WHITENOISE_MANIFEST_STRICT = True
# Email in memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Additional test middleware
# MIDDLEWARE.append("core.htmlvalidator.HtmlValidatorMiddleware")

# Database
DATABASES["default"]["TEST"] = {
  "NAME": "test_cousinsmatter",
  "MIRROR": None,
  "CHARSET": None,
}
DATABASES["default"]["OPTIONS"].pop("pool", None)
