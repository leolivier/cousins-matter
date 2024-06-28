from django.conf import settings as django_settings

# Write here the settings you want to expose to the templates.
EXPOSED_SETTINGS = [
  # 'BASE_DIR',
  'SITE_NAME',
  'SITE_DOMAIN',
  'SITE_FOOTER',
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
  # 'DEFAULT_AVATAR_URL',
  # 'PDF_SIZE',
  # 'GALLERIES_DIR',
  'GALLERIES_THUMBNAIL_SIZE',
  # 'MAX_PHOTO_FILE_SIZE',
  # 'DEFAULT_GALLERY_COVER_URL',
  # 'DEFAULT_GALLERY_PAGE_SIZE',
  'MAX_GALLERY_BULK_UPLOAD_SIZE',
  'MAX_CSV_FILE_SIZE',
  # 'MESSAGE_MAX_SIZE',
  # 'MESSAGE_COMMENTS_MAX_SIZE',
  'DARK_MODE',
]


def settings(request):
    """expose settings to templates"""
    settings_in_templates = {}
    for attr in EXPOSED_SETTINGS:
        if (hasattr(django_settings, attr)):
            settings_in_templates[attr] = getattr(django_settings, attr)
    return {
        'settings': settings_in_templates,
    }
