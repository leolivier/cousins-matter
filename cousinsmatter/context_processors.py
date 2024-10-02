from typing import Any
from django.conf import settings as django_settings
from django.test import override_settings as django_override_settings

# Write here the settings you want to expose to the templates.
EXPOSED_SETTINGS = [
  'DATA_UPLOAD_MAX_MEMORY_SIZE',
  # 'BASE_DIR',
  'SITE_NAME',
  'SITE_DOMAIN',
  'SITE_FOOTER',
  'SITE_LOGO',
  'SITE_COPYRIGHT',
  'DEBUG',
  'MAX_REGISTRATION_AGE',
  'LANGUAGE_CODE',
  'TIME_ZONE',
  'DEFAULT_FROM_EMAIL',
  'BIRTHDAY_DAYS',
  'INCLUDE_BIRTHDAYS_IN_HOMEPAGE',
  # 'STATIC_URL',
  # 'MEDIA_URL',
  # 'AVATARS_DIR',
  'AVATARS_SIZE',
  'AVATARS_MINI_SIZE',
  'DEFAULT_AVATAR_URL',
  'DEFAULT_MINI_AVATAR_URL',
  # 'PDF_SIZE',
  # 'GALLERIES_DIR',
  'GALLERIES_THUMBNAIL_SIZE',
  # 'MAX_PHOTO_FILE_SIZE',
  # 'DEFAULT_GALLERY_COVER_URL',
  # 'DEFAULT_GALLERY_PAGE_SIZE',
  'MAX_GALLERY_BULK_UPLOAD_SIZE',
  'MAX_CSV_FILE_SIZE',
  'MESSAGE_MAX_SIZE',
  'MESSAGE_COMMENTS_MAX_SIZE',
  'COMMENT_MAX_SIZE',
  'DARK_MODE',
  'ALLOW_MEMBERS_TO_CREATE_MEMBERS',
  'ALLOW_MEMBERS_TO_INVITE_MEMBERS',
  'PUBLIC_MEDIA_URL',
  'PAGE_MAX_SIZE',
  'LANGUAGES',
]


def _compute_settings_in_templates():
  """
  Computes and returns a dictionary containing the settings which can be exposed to the templates.
  """
  return {attr: getattr(django_settings, attr) for attr in EXPOSED_SETTINGS if (hasattr(django_settings, attr))}


# initialize the settings in templates only once to optimize performance
_settings_in_templates = _compute_settings_in_templates()


def settings(request):
    """expose settings to templates"""
    # settings are pre computed in global variable
    return {'settings': _settings_in_templates}


class override_settings(django_override_settings):
  """override settings as usual for tests but also expose them in templates"""
  def enable(self) -> Any | None:
    super().enable()
    global _settings_in_templates
    _settings_in_templates = _compute_settings_in_templates()

  def disable(self) -> Any | None:
    super().disable()
    global _settings_in_templates
    _settings_in_templates = _compute_settings_in_templates()
