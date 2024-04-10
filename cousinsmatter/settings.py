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

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# load keys from .env
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
environ.Env.read_env(Path(BASE_DIR, '.env'))

SITE_NAME = env('SITE_NAME', default='Cousins Matter')

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

MAX_REGISTRATION_AGE = env('MAX_REGISTRATION_AGE', default=2*24*3600)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

LANGUAGE_CODE = env('LANGUAGE_CODE', default='en-us')

TIME_ZONE = env('TIME_ZONE', default='Europe/Paris')

HOME_TITLE=env('HOME_TITLE', default='Cousins Matter!')
HOME_CONTENT_UNSIGNED=env.str('HOME_CONTENT_UNSIGNED', multiline=True, default="")
HOME_CONTENT_SIGNED=env.str('HOME_CONTENT_SIGNED', multiline=True, default="")
HOME_LOGO=env('HOME_LOGO', default='static/images/cousinsmatter.jpg')
SITE_COPYRIGHT=env('SITE_COPYRIGHT', default='Site Copyright © 2024 Cousins Matter. All rights reserved.')

# Email properties
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default="cousinsmatter@localhost")

# log levels
DJANGO_LOG_LEVEL = env('DJANGO_LOG_LEVEL', default='INFO')
CM_LOG_LEVEL = env('CM_LOG_LEVEL', default='INFO')

# Number of days for birthdays
BIRTHDAY_DAYS = env('BIRTHDAY_DAYS', default=50)

# Application definition

INSTALLED_APPS = [
	'accounts.apps.AccountsConfig',
	'cm_main.apps.CmMainConfig',
	'members.apps.MembersConfig',
    'polls.apps.PollsConfig',
    'crispy_forms',
    'crispy_bulma',
    'django_icons',
	"verify_email.apps.VerifyEmailConfig",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
	'captcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
            ],
        },
    },
]

WSGI_APPLICATION = 'cousinsmatter.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(BASE_DIR, 'data', 'db.sqlite3'),
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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_ROOT = Path(BASE_DIR, 'static')
STATIC_URL = 'static/'
# STATICFILES_DIRS = []

MEDIA_ROOT = Path(BASE_DIR, 'media').absolute()
MEDIA_URL = 'media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CRISPY_TEMPLATE_PACK = 'bulma'

LOGIN_REDIRECT_URL = '/'
# LOGIN_URL = '/accounts/login'
LOGIN_URL = 'accounts:login'
#LOGOUT_REDIRECT_URL = '/'

DJANGO_ICONS = {
    "ICONS": {
        "account": {"name": "mdi mdi-account"},
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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
AVATARS_SIZE = 300
AVATARS_MAX_LOAD_SIZE = 1024 * 1024 * 2

VERIFICATION_SUCCESS_TEMPLATE = "accounts/email_verification_successful.html"
VERIFICATION_FAILED_TEMPLATE = "accounts/email_verification_failed.html"
REQUEST_NEW_EMAIL_TEMPLATE = "accounts/request_new_email.html"
HTML_MESSAGE_TEMPLATE = "accounts/email_verification_msg.html"

CAPTCHA_LENGTH=6
