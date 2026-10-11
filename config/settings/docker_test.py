from .dev_base import *  # noqa: F403, F405

DEBUG = env.bool("DEBUG", False)
TESTING = True
DEBUG_TOOLBAR = False
DEBUG_HTMX = False
# Same as local_test.py: tests assert untranslated strings, pin the language
# so a LANGUAGE_CODE in the compose .env cannot change the rendered pages.
LANGUAGE_CODE = "en"
# See local_test.py: tests run WITHOUT collectstatic, so use the plain storage
# (DEBUG is forced to False by the test runner, which would otherwise make the
# manifest storage raise "Missing staticfiles manifest entry" or return hashed
# URLs StaticLiveServerTestCase can't serve).
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"
# Email in memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# allauth ships a default "login: 30/m/ip" rate limit. The UI suite performs
# ~190 logins from localhost, which trips it (HTTP 429) and makes tests flaky
# in CI. Disable allauth rate limiting entirely in tests.
ACCOUNT_RATE_LIMITS = False

# OAuth UI tests (e.g. members registration vs create view gating) need a
# registered provider. allauth's provider registry and URL patterns are built
# once at boot from INSTALLED_APPS, so the provider must be installed here in
# settings — a per-test modify_settings cannot add it after the fact. CI has
# no OAUTH_PROVIDERS env vars, so add google with a dummy app when missing
# (locally the .env already configures it through base.py).
if "allauth.socialaccount.providers.google" not in INSTALLED_APPS:
  INSTALLED_APPS.append("allauth.socialaccount.providers.google")
SOCIALACCOUNT_PROVIDERS.setdefault("google", {"APPS": [{"client_id": "dummy", "secret": "dummy", "key": ""}]})  # nosec B105 - dummy test credentials
# Database
DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="postgres")
DATABASES["default"]["OPTIONS"].pop("pool", None)
DATABASES["default"]["TEST"] = {
  "NAME": "test_cousinsmatter",
  "MIRROR": None,
  "CHARSET": None,
}

# Keep the robust dict-format config from base.py; only retarget the address.
# docker (CI): Redis is reachable through its compose service name (dev_base
# retargets the default to localhost, which only holds on the host)
REDIS_HOST = env.str("REDIS_HOST", default="redis")
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]["address"] = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Django Q2 settings for tests
Q_CLUSTER["sync"] = True
