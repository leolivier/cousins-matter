"""
Django basic settings for cousinsmatter project.
"""

import environ
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# load keys from .env
# We don't use overwrite=True so that variables already set in the environment (e.g. by Docker) are preserved
environ.Env.read_env(BASE_DIR / ".env")


SECRET_KEY = env.str("SECRET_KEY")
# when rotating the secret key, you can provide the old key here to avoid breaking the site
SECRET_KEY_FALLBACKS = env.list("PREVIOUS_SECRET_KEYS", default=[])

DARK_MODE = env.bool("DARK_MODE", False)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_REL = "static"
STATIC_ROOT = BASE_DIR / STATIC_REL
STATIC_URL = "static/"
# STATICFILES_DIRS = []

MEDIA_REL = Path("media")
MEDIA_ROOT = BASE_DIR / MEDIA_REL
MEDIA_URL = f"/protected_{MEDIA_REL}/"

PUBLIC_MEDIA_ROOT = MEDIA_ROOT / "public"
PUBLIC_MEDIA_URL = f"/{MEDIA_REL}/public/"

SITE_NAME = env.str("SITE_NAME", default="Cousins Matter")
SITE_DOMAIN = env.str("SITE_DOMAIN", None)
SITE_PORT = env.int("SITE_PORT", default=0 if SITE_DOMAIN else 8000)
SITE_PORTS = f":{SITE_PORT}" if SITE_PORT else ""
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CORS_ALLOWED_ORIGINS = env.list(
  "CORS_ALLOWED_ORIGINS",
  default=[
    f"http://localhost{SITE_PORTS}",
    f"http://127.0.0.1{SITE_PORTS}",
  ],
)
CSRF_TRUSTED_ORIGINS = env.list(
  "CSRF_TRUSTED_ORIGINS",
  default=[
    f"http://localhost{SITE_PORTS}",
    f"http://127.0.0.1{SITE_PORTS}",
  ],
)

LANGUAGES = [
  ("fr", "Français"),
  ("en", "English"),
  ("es", "Español"),
  ("de", "Deutsch"),
  ("it", "Italiano"),
  ("pt", "Português"),
]
LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en")
TIME_ZONE = env.str("TIME_ZONE", default="Europe/Paris")

SITE_COPYRIGHT = env.str("SITE_COPYRIGHT", default=None)
SITE_FOOTER = env.str("SITE_FOOTER", default=None)
SITE_LOGO = env.str("SITE_LOGO", default="core/images/cousinades.jpg")

# Defult Email properties
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="cousinsmatter@localhost")

# Default log levels
DJANGO_LOG_LEVEL = env.str("DJANGO_LOG_LEVEL", default="INFO")
CM_LOG_LEVEL = env.str("CM_LOG_LEVEL", default="INFO")

STORAGES = {
  "staticfiles": {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
  },
  "default": {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {
      "location": MEDIA_ROOT,
      "base_url": MEDIA_URL,
    },
  }
  if env.str("MEDIA_STORAGE", default=None) is None
  else {
    "BACKEND": env.str("MEDIA_STORAGE"),
    "OPTIONS": env.json("MEDIA_STORAGE_OPTIONS", default={}),
  },
}

SITE_ID = 1
LOCAL_APPS = [
  "core",
  "members",
  "chat",
  "galleries",
  "classified_ads",
  "cousinsmatter",
  "forum",
  "genealogy",
  "pages",
  "polls",
  "troves",
]

# Application definition

INSTALLED_APPS = [
  *LOCAL_APPS,
  "crispy_forms",
  "crispy_bulma",
  "django.contrib.admin",
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "django.contrib.sessions",
  "django.contrib.messages",
  "django.contrib.staticfiles",
  "django.contrib.sites",
  "django.contrib.flatpages",
  "captcha",
  "channels",
  "django_q",
  "django_htmx",
]

MIDDLEWARE = [
  "django.middleware.security.SecurityMiddleware",
  "whitenoise.middleware.WhiteNoiseMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "django.middleware.locale.LocaleMiddleware",
  "corsheaders.middleware.CorsMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "django.contrib.auth.middleware.LoginRequiredMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
  "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
  "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "cousinsmatter.urls"

TEMPLATES = [
  {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
      "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "django.template.context_processors.media",
        "core.context_processors.settings",
      ],
    },
  },
]

WSGI_APPLICATION = "cousinsmatter.wsgi.application"

ASGI_APPLICATION = "cousinsmatter.asgi.application"

CHANNEL_LAYERS: dict[str, Any] = {
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

DATABASES: dict[str, Any] = {
  "default": {
    "ENGINE": "django.db.backends.postgresql",
    "USER": env.str("POSTGRES_USER", default="cousinsmatter"),
    "PASSWORD": env.str("POSTGRES_PASSWORD"),
    "HOST": env.str("POSTGRES_HOST", default="postgres"),
    "PORT": env.int("POSTGRES_PORT", default=5432),
    "NAME": env.str("POSTGRES_DB", default="cousinsmatter"),
    "CONN_MAX_AGE": 0,
    "OPTIONS": {
      "connect_timeout": 10,
      "pool": {
        "min_size": 2,
        "max_size": 20,
        "timeout": 30,
      },
    },
  }
}

# Django Q2 settings
Q_CLUSTER: dict[str, Any] = {
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

# Password validation

AUTH_PASSWORD_VALIDATORS = [
  {
    "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
  },
]

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_FAIL_SILENTLY = True
CRISPY_TEMPLATE_PACK = "bulma"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("bulma",)

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "members:login"
MAX_REGISTRATION_AGE = env.int("MAX_REGISTRATION_AGE", default=2 * 24 * 3600)

LOGGING: dict[str, Any] = {
  "version": 1,
  "disable_existing_loggers": False,
  "formatters": {
    "verbose": {
      "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
      "style": "{",
    },
    "simple": {
      "format": "{levelname} {message}",
      "style": "{",
    },
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "simple",
    },
    "file": {
      "class": "logging.FileHandler",
      "filename": "general.log",
      "formatter": "verbose",
    },
  },
  "root": {
    "handlers": ["console"],
    "level": "WARNING",
  },
  "loggers": {
    "django": {
      "handlers": ["console", "file"],
      "level": DJANGO_LOG_LEVEL,
      "propagate": False,
    },
    **{
      app: {
        "handlers": ["console", "file"],
        "level": CM_LOG_LEVEL,
        "propagate": False,
      }
      for app in LOCAL_APPS
    },
  },
}

# default max upload size is 2.5MB but could be overridden.
# WARNING:THIS VARIABLE IS RECOMPUTED AT THE END OF THE FILE!
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=2.5 * 1024 * 1024)  # 2.5MB

# Number of days for birthdays
BIRTHDAY_DAYS = env.int("BIRTHDAY_DAYS", default=50)
AVATARS_DIR = "avatars"
# If you update these sizes, update them accordingly
# for .avatar and .mini-avatar CSS classes in
# core/static/core/css/core.css
AVATARS_SIZE = 300
AVATARS_MINI_SIZE = 64
DEFAULT_AVATAR_URL = "/static/members/default-avatar.jpg"
DEFAULT_MINI_AVATAR_URL = "/static/members/default-mini-avatar.jpg"

# Email verification templates
VERIFICATION_SUCCESS_TEMPLATE = "members/registration/email_verification_successful.html"
VERIFICATION_FAILED_TEMPLATE = "members/registration/email_verification_failed.html"
REQUEST_NEW_EMAIL_TEMPLATE = "members/registration/request_new_email.html"
HTML_MESSAGE_TEMPLATE = "members/email/email_verification_msg.html"
SUBJECT = _("Email verification")

CAPTCHA_LENGTH = 6

PDF_SIZE = env.str("PDF_SIZE", "A4")  # or 'letter'

GALLERIES_DIR = "galleries"
GALLERIES_THUMBNAIL_SIZE = 300
MAX_PHOTO_FILE_SIZE = env.int("MAX_PHOTO_FILE_SIZE", 1024 * 1024 * 5)  # 5MB
MAX_VIDEO_FILE_SIZE = env.int("MAX_VIDEO_FILE_SIZE", 1024 * 1024 * 20)  # 20MB
DEFAULT_GALLERY_COVER_URL = "/static/galleries/default-gallery-cover.jpg"
DEFAULT_GALLERY_PAGE_SIZE = env.int("DEFAULT_GALLERY_PAGE_SIZE", 25)
MAX_GALLERY_BULK_UPLOAD_SIZE = env.int("MAX_GALLERY_BULK_UPLOAD_SIZE", 20 * 1024 * 1024)  # 20MB
MAX_CSV_FILE_SIZE = env.int("MAX_CSV_FILE_SIZE", 2 * 1024 * 1024)  # 2MB
SLIDESHOW_DELAY = env.int("SLIDESHOW_DELAY", default=5)

# members settings
AUTH_USER_MODEL = "members.Member"
DEFAULT_MEMBERS_PAGE_SIZE = env.int("DEFAULT_MEMBERS_PAGE_SIZE", 25)
ALLOW_MEMBERS_TO_CREATE_MEMBERS = env.bool("ALLOW_MEMBERS_TO_CREATE_MEMBERS", True)
ALLOW_MEMBERS_TO_INVITE_MEMBERS = env.bool("ALLOW_MEMBERS_TO_INVITE_MEMBERS", True)

# forum settings
DEFAULT_POSTS_PER_PAGE = env.int("DEFAULT_POSTS_PER_PAGE", 25)
# chat settings
DEFAULT_CHATMESSAGES_PER_PAGE = env.int("DEFAULT_CHATMESSAGES_PER_PAGE", 25)
DEFAULT_CHATROOMS_PER_PAGE = env.int("DEFAULT_CHATROOMS_PER_PAGE", 25)
MESSAGE_MAX_SIZE = env.int("MESSAGE_MAX_SIZE", DATA_UPLOAD_MAX_MEMORY_SIZE)
MESSAGE_COMMENTS_MAX_SIZE = env.int("MESSAGE_COMMENTS_MAX_SIZE", 400)

CONTACT_MAX_SIZE = env.int("CONTACT_MAX_SIZE", 1024 * 1024)  # 1MB

# page settings
PAGES_URL_PREFIX = "pages/"
PRIVACY_URL = "/about/privacy-policy/"
MENU_PAGE_URL_PREFIX = "/publish"
PRIVATE_PAGE_URL_PREFIX = "/private"
ADMIN_MESSAGE_PAGE_URL_PREFIX = "/admin-message"
AUTHENTICATED_HOME_PAGE = "/home/authenticated/"
UNAUTHENTICATED_HOME_PAGE = "/home/unauthenticated/"
PAGE_MAX_SIZE = env.int("PAGE_MAX_SIZE", 10 * 1024 * 1024)  # 10MB

DATA_UPLOAD_MAX_MEMORY_SIZE = max(DATA_UPLOAD_MAX_MEMORY_SIZE, MESSAGE_MAX_SIZE, PAGE_MAX_SIZE)

# read version from release.txt
with open(BASE_DIR / "release.txt", "r") as f:
  APP_VERSION = f.read().strip()

# Troves settings
TROVE_DIRECTORY_REL = "troves"
TROVE_DIRECTORY = Path(TROVE_DIRECTORY_REL)
TROVE_PICTURE_DIRECTORY_REL = "pictures"
TROVE_THUMBNAIL_DIRECTORY_REL = "thumbnails"
TROVE_FILES_DIRECTORY_REL = "files"
TROVE_PICTURE_DIRECTORY = TROVE_DIRECTORY / TROVE_PICTURE_DIRECTORY_REL
TROVE_THUMBNAIL_DIRECTORY = TROVE_PICTURE_DIRECTORY / TROVE_THUMBNAIL_DIRECTORY_REL
TROVE_FILES_DIRECTORY = TROVE_DIRECTORY / TROVE_FILES_DIRECTORY_REL
TROVE_URL_PREFIX = f"{TROVE_DIRECTORY}/"
TROVE_PICTURE_URL_PREFIX = f"{TROVE_URL_PREFIX}{TROVE_PICTURE_DIRECTORY_REL}/"
TROVE_THUMBNAIL_URL_PREFIX = f"{TROVE_PICTURE_URL_PREFIX}{TROVE_THUMBNAIL_DIRECTORY_REL}/"
TROVE_FILE_URL_PREFIX = f"{TROVE_URL_PREFIX}{TROVE_FILES_DIRECTORY_REL}/"
TROVE_FILE_MAX_SIZE = env.int("TROVE_FILE_MAX_SIZE", 20 * 1024 * 1024)  # 20MB
TROVE_PICTURE_FILE_MAX_SIZE = env.int("TROVE_PICTURE_FILE_MAX_SIZE", MAX_PHOTO_FILE_SIZE)
TROVE_THUMBNAIL_SIZE = env.int("TROVE_THUMBNAIL_SIZE", GALLERIES_THUMBNAIL_SIZE)
DEFAULT_TROVE_PAGE_SIZE = env.int("DEFAULT_TROVE_PAGE_SIZE", 10)
TROVE_DESCRIPTION_MAX_SIZE = MESSAGE_MAX_SIZE

EMAIL_FIELD_NAME = "email"  # force name to bypass translation

LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP = env.str("LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP", default=None)
LOGIN_HISTORY_PURGE_DAYS = env.int("LOGIN_HISTORY_PURGE_DAYS", 365)

MAX_PHOTO_PER_AD = env.int("MAX_PHOTO_PER_AD", 10)

FEATURES_FLAGS = env.dict(
  "FEATURES_FLAGS",
  cast={"value": bool},
  default={
    "show_birthdays_in_homepage": True,
    "show_galleries": True,
    "show_forums": True,
    "show_public_chats": True,
    "show_private_chats": True,
    "show_classified_ads": True,
    "show_polls": True,
    "show_event_planners": True,
    "show_pages": True,
    "show_treasures": True,
    "show_site_stats": True,
    "show_export_members": True,
    "show_change_language": True,
    "show_genealogy": True,
  },
)

# GENEALOGY
# Number of generations to show in the family chart
FAMILY_CHART_GENERATIONS = env.int("FAMILY_CHART_GENERATIONS", default=4)
# Default root person ID to show in the family chart if none is specified
FAMILY_CHART_ROOT_PERSON_ID = env.int("FAMILY_CHART_ROOT_PERSON_ID", default=None)
GEDCOM_FILE = env.str("GEDCOM_FILE", default="genealogy.ged")
