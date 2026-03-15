from .base import *  # noqa: F403, F405

DEBUG = False
TESTING = False
DEBUG_TOOLBAR = False
DEBUG_HTMX = False

SECRET_KEY = env.str("SECRET_KEY")
# when rotating the secret key, you can provide the old key here to avoid breaking the site
SECRET_KEY_FALLBACKS = env.list("PREVIOUS_SECRET_KEYS", default=[])

WHITENOISE_MANIFEST_STRICT = True

SITE_DOMAIN = env.str("SITE_DOMAIN")
assert SITE_DOMAIN
SITE_PORT = env.int("SITE_PORT", default=0)
SITE_PORT = f":{SITE_PORT}" if SITE_PORT else ""
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[SITE_DOMAIN, *ALLOWED_HOSTS])
CORS_ALLOWED_ORIGINS = env.list(
  "CORS_ALLOWED_ORIGINS",
  default=[
    *CORS_ALLOWED_ORIGINS,
    f"https://{SITE_DOMAIN}{SITE_PORT}",
  ],
)
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_DOMAIN = env.str("SESSION_COOKIE_DOMAIN", None)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS= # TODO
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Production Email properties
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="cousinsmatter@localhost")

# log levels
DJANGO_LOG_LEVEL = env.str("DJANGO_LOG_LEVEL", default="WARN")
CM_LOG_LEVEL = env.str("CM_LOG_LEVEL", default="WARN")
LOGGING["loggers"]["django"]["level"] = DJANGO_LOG_LEVEL
for app in LOCAL_APPS:
  LOGGING["loggers"][app]["level"] = CM_LOG_LEVEL

INSTALLED_APPS = [
  "daphne",
  *INSTALLED_APPS,
  "verify_email",
  "corsheaders",
]

CHANNEL_LAYERS = {
  "default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {
      "hosts": [
        (
          env.str("REDIS_HOST", default="redis"),
          env.int("REDIS_PORT", default=6379),
        )
      ],
    },
  },
}

CRISPY_FAIL_SILENTLY = True

# Django Q2 settings
Q_CLUSTER = {
  "name": slugify(SITE_NAME),
  "workers": 2,
  # 'recycle': 500,
  "timeout": 60,
  "max_attempts": 5,
  # 'compress': False,
  # 'cpu_affinity': 1,
  # 'save_limit': 250,
  # 'queue_limit': 500,
  # 'label': 'Django Q2',
  "redis": {
    "host": env.str("REDIS_HOST", default="redis"),
    "port": env.int("REDIS_PORT", default=6379),
    # 'db': 0,
  },
  "sync": env.bool("Q_SYNC", False),  # set to True in development
}
