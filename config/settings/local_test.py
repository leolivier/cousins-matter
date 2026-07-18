from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False
# Tests must run WITHOUT collectstatic. Django's test runner forces DEBUG=False
# (DiscoverRunner -> setup_test_environment(debug=False)), which disables
# HashedFilesMixin._url's DEBUG shortcut. With CompressedManifestStaticFilesStorage
# every {% static %} call then hits stored_name() -> either "Missing staticfiles
# manifest entry" (no collectstatic) or hashed URLs that StaticLiveServerTestCase
# can't serve (404 -> 'htmx is not defined'). Use the plain storage so URLs stay
# unhashed and StaticLiveServerTestCase serves them from source files via the
# staticfiles finders. (The production storage is still exercised by the
# collectstatic CI job.)
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"
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
