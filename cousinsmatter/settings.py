"""
Django settings for cousinsmatter project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""
import environ
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# load keys from .env
env = environ.Env(
  # set casting, default value
  DEBUG=(bool, False)
)
environ.Env.read_env(BASE_DIR / '.env', overwrite=True)

DEBUG = env.bool('DEBUG', False)
if DEBUG:
  print(f"WARNING! DEBUG={DEBUG}. This is not suited for production!")
SECRET_KEY = env.str('SECRET_KEY')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_REL = 'static'
STATIC_ROOT = BASE_DIR / STATIC_REL
STATIC_URL = 'static/'
# STATICFILES_DIRS = []

MEDIA_REL = 'media'
MEDIA_ROOT = BASE_DIR / MEDIA_REL
if DEBUG:
  MEDIA_URL = MEDIA_REL + '/'
else:
  MEDIA_URL = f'protected_{MEDIA_REL}/'

PUBLIC_MEDIA_ROOT = MEDIA_ROOT / 'public'
PUBLIC_MEDIA_URL = f'/{MEDIA_REL}/public/'

SITE_NAME = env.str('SITE_NAME', default='Cousins Matter')
SITE_DOMAIN = env.str('SITE_DOMAIN', None)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=['127.0.0.1', 'localhost'])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_DOMAIN = env.str('SESSION_COOKIE_DOMAIN', None)

LANGUAGES = [
    ("fr", "Français"),
    ("en-us", "English (US)"),
    ("es", "Español"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
]
LANGUAGE_CODE = env.str('LANGUAGE_CODE', default='en-us')
TIME_ZONE = env.str('TIME_ZONE', default='Europe/Paris')

INCLUDE_BIRTHDAYS_IN_HOMEPAGE = env.bool('INCLUDE_BIRTHDAYS_IN_HOMEPAGE', True)

SITE_COPYRIGHT = env.str('SITE_COPYRIGHT', default=None)
SITE_FOOTER = env.str('SITE_FOOTER', default=None)
SITE_LOGO = env.str('SITE_LOGO', default='cm_main/images/cousinades.jpg')
# Email properties
EMAIL_HOST = env.str('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default="cousinsmatter@localhost")

# log levels
DJANGO_LOG_LEVEL = env.str('DJANGO_LOG_LEVEL', default='INFO')
CM_LOG_LEVEL = env.str('CM_LOG_LEVEL', default='INFO')

# default max upload size is 2.5MB but could be overridden.
# WARNING:THIS VARIABLE IS RECOMPUTED AT THE END OF THE FILE!
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int('DATA_UPLOAD_MAX_MEMORY_SIZE', default=2.5 * 1024 * 1024)  # 2.5MB

# Number of days for birthdays
BIRTHDAY_DAYS = env.int('BIRTHDAY_DAYS', default=50)

SITE_ID = 1
# Application definition

INSTALLED_APPS = [
  'daphne',
  'cm_main',
  'members',
  'galleries',
  'polls',
  'forum',
  'chat',
  'pages',
  'crispy_forms',
  'crispy_bulma',
  'verify_email',
  'corsheaders',
  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'django.contrib.sites',
  'django.contrib.flatpages',
  'captcha',
  'channels',
]

MIDDLEWARE = [
  'django.middleware.security.SecurityMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'corsheaders.middleware.CorsMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
  'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
  'django.middleware.locale.LocaleMiddleware',
]
# if DEBUG:
#   MIDDLEWARE.append('cousinsmatter.htmlvalidator.HtmlValidatorMiddleware')

ROOT_URLCONF = 'cousinsmatter.urls'

TEMPLATES = [
  {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
      'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'django.template.context_processors.media',
        'cousinsmatter.context_processors.settings',
      ],
    },
  },
]

WSGI_APPLICATION = 'cousinsmatter.wsgi.application'

ASGI_APPLICATION = "cousinsmatter.asgi.application"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'data' / 'db.sqlite3',
  }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
  {
    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
  },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CRISPY_TEMPLATE_PACK = 'bulma'

LOGIN_REDIRECT_URL = '/'
# LOGIN_URL = '/members/login'
LOGIN_URL = 'members:login'
# LOGOUT_REDIRECT_URL = '/'
MAX_REGISTRATION_AGE = env.int('MAX_REGISTRATION_AGE', default=2*24*3600)

DJANGO_ICONS = {
    # footer icons
    "copyleft": "copyleft",
    # main icons
    "back": "arrow-up-left",
    "delete": "trash-can-outline",
    "edit": "pencil-outline",
    "save": "content-save-outline",
    "submit": "check-circle-outline",
    "create": "checkbox-marked-circle-auto-outline",
    "create-plus": "checkbox-marked-circle-plus-outline",
    "update": "check-underline-circle-outline",
    "cancel": "close-circle-outline",
    "clear": "backspace-outline",
    "new": "plus-box-outline",
    "send-message": "send-variant-outline",
    "search": "magnify",
    "print": "printer",
    "pdf": "file-pdf-box",
    "help": "help-circle-outline",
    "settings": "cog-outline",
    "menu-open": "menu-open",
    "menu-close": "menu-close",
    "information": "information-outline",
    "contact": "card-account-mail-outline",
    "private": "eye-lock-outline",
    "upload": "upload-box-outline",
    "about": "information-variant",
    "admin": "application-cog-outline",
    "stats": "chart-box-outline",
    "leave-group": "account-multiple-minus-outline",
    # emoticons
    "thumb-up": "thumb-up-outline",
    "thumb-down": "thumb-down-outline",
    "poop": "emoticon-poop-outline",
    "confused": "robot-confused-outline",
    "cool": "emoticon-cool-outline",
    "wink": "emoticon-wink-outline",
    # auth icons
    "signin": "login",
    "signout": "logout",
    "signup": "account-plus",
    "change-password": "lock-reset",
    # pagination icons
    "pagination-previous": "chevron-left-box-outline",
    "pagination-next": "chevron-right-box-outline",
    # follow icons
    "follow": "link-variant",
    "unfollow": "link-variant-off",
    # member icons
    "member": "account-outline",
    "member-link": "open-in-new",
    "new-member": "account-plus-outline",
    "invite-member": "card-account-mail-outline",
    "invite-request": "account-box-plus-outline",
    "import-members": "account-multiple-plus-outline",
    "activate-member": "account-reactivate",
    "members": "account-group-outline",
    "profile": "account-box-edit-outline",
    "birthday": "cake-variant-outline",
    "birthday-variant": "cake-variant",
    "directory": "format-list-text",
    "directory-variant": "book-alphabet",
    "deceased": "shield-cross-outline",  # or "coffin"?
    # gallery icons
    "galleries": "folder-multiple-image",
    "new-gallery": "file-image-plus-outline",
    "edit-gallery": "image-edit",
    "import-galleries": "folder-plus-outline",
    "new-photo": "image-plus-outline",
    "edit-photo": "image-edit-outline",
    # forum icons
    "forum": "forum-outline",
    "new-forum": "forum-plus-outline",
    # chat icons
    "new-chat-room": "chat-plus-outline",
    "chat-room": "chat",
    # page icons
    "page": "page-next",
    "page-level": "page-next-outline",
    "new-page": "book-open-page-variant-outline",
    "edit-page": "note-edit-outline",
    # arrows
    "arrow-down": "arrow-down-thin",
    "arrow-up": "arrow-up-thin",
    "arrow-up-down": "swap-vertical"
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
    },
    "file": {
      "class": "logging.FileHandler",
      "filename": "general.log",
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
    "members": {
      "handlers": ["console", "file"],
      "level": CM_LOG_LEVEL,
      "propagate": False,
    },
  },
}

AVATARS_DIR = 'avatars'
# If you update these sizes, update them accordingly
# for .avatar and .mini-avatar CSS classes in
# cm_main/static/cm_main/css/cm_main.css
AVATARS_SIZE = 300
AVATARS_MINI_SIZE = 64
DEFAULT_AVATAR_URL = '/static/members/default-avatar.jpg'
DEFAULT_MINI_AVATAR_URL = '/static/members/default-mini-avatar.jpg'

# Email verification templates
VERIFICATION_SUCCESS_TEMPLATE = "members/registration/email_verification_successful.html"
VERIFICATION_FAILED_TEMPLATE = "members/registration/email_verification_failed.html"
REQUEST_NEW_EMAIL_TEMPLATE = "members/registration/request_new_email.html"
HTML_MESSAGE_TEMPLATE = "members/email/email_verification_msg.html"
SUBJECT = _('Email verification')

CAPTCHA_LENGTH = 6

PDF_SIZE = env.str('PDF_SIZE', 'A4')  # or 'letter'

GALLERIES_DIR = 'galleries'
GALLERIES_THUMBNAIL_SIZE = 300
MAX_PHOTO_FILE_SIZE = env.int('MAX_PHOTO_FILE_SIZE', 1024 * 1024 * 5)  # 5MB
DEFAULT_GALLERY_COVER_URL = '/static/galleries/default-gallery-cover.jpg'
DEFAULT_GALLERY_PAGE_SIZE = env.int('DEFAULT_GALLERY_PAGE_SIZE', 25)
MAX_GALLERY_BULK_UPLOAD_SIZE = env.int('MAX_GALLERY_BULK_UPLOAD_SIZE', 20*1024*1024)  # 20MB
MAX_CSV_FILE_SIZE = env.int('MAX_CSV_FILE_SIZE', 2*1024*1024)  # 2MB

DARK_MODE = env.bool('DARK_MODE', False)

AUTH_USER_MODEL = 'members.Member'

DEFAULT_MEMBERS_PAGE_SIZE = env.int('DEFAULT_MEMBERS_PAGE_SIZE', 25)
DEFAULT_POSTS_PER_PAGE = env.int('DEFAULT_POSTS_PER_PAGE', 25)
DEFAULT_CHATMESSAGES_PER_PAGE = env.int('DEFAULT_CHATMESSAGES_PER_PAGE', 25)
DEFAULT_CHATROOMS_PER_PAGE = env.int('DEFAULT_CHATROOMS_PER_PAGE', 25)
MESSAGE_MAX_SIZE = env.int('MESSAGE_MAX_SIZE', DATA_UPLOAD_MAX_MEMORY_SIZE)
MESSAGE_COMMENTS_MAX_SIZE = env.int('MESSAGE_COMMENTS_MAX_SIZE', 400)

CONTACT_MAX_SIZE = env.int('CONTACT_MAX_SIZE', 1024*1024)  # 1MB

PAGES_URL_PREFIX = 'pages/'
PRIVACY_URL = f'/{LANGUAGE_CODE}/about/privacy-policy/'
MENU_PAGE_URL_PREFIX = '/publish'
PRIVATE_PAGE_URL_PREFIX = '/private'
ADMIN_MESSAGE_PAGE_URL_PREFIX = '/admin-message'
AUTHENTICATED_HOME_PAGE = f'/{LANGUAGE_CODE}/home/authenticated/'
UNAUTHENTICATED_HOME_PAGE = f'/{LANGUAGE_CODE}/home/unauthenticated/'
PAGE_MAX_SIZE = env.int('PAGE_MAX_SIZE', 10*1024*1024)  # 10MB

DATA_UPLOAD_MAX_MEMORY_SIZE = max(DATA_UPLOAD_MAX_MEMORY_SIZE, MESSAGE_MAX_SIZE, PAGE_MAX_SIZE)

ALLOW_MEMBERS_TO_CREATE_MEMBERS = env.bool('ALLOW_MEMBERS_TO_CREATE_MEMBERS', True)
ALLOW_MEMBERS_TO_INVITE_MEMBERS = env.bool('ALLOW_MEMBERS_TO_INVITE_MEMBERS', True)

# read version from release.txt
with open(BASE_DIR / 'release.txt', 'r') as f:
  APP_VERSION = f.read().strip()
