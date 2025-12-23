# this data migrations will change the URL of the following pages:
# /pages/message/ -> settings.ADMIN_MESSAGE_PAGE_URL_PREFIX
# Pages starting with settings.PRIVATE_PAGE_URL_PREFIX and settings.MENU_PAGE_URL_PREFIX will remain unaffected
# Remaining pages starting with /pages will get /pages removed
# other non predefined pages will be prefixed by settings.MENU_PAGE_URL_PREFIX if not already

from django.conf import settings
from django.db import migrations


def migrateAdminMessages(apps, schema_editor):
  CustomFlatPage = apps.get_model("pages", "FlatPage")
  for page in (
    CustomFlatPage.objects.filter(predefined=False)
    .exclude(url__startswith="/pages/message/")
    .exclude(url__startswith=settings.PRIVATE_PAGE_URL_PREFIX)
    .exclude(url__startswith=settings.MENU_PAGE_URL_PREFIX)
  ):
    page.url = settings.MENU_PAGE_URL_PREFIX + page.url
    page.save(update_fields=["url"])
  for page in CustomFlatPage.objects.filter(url__startswith="/pages/message/"):
    page.url = page.url.replace("/pages/message", settings.ADMIN_MESSAGE_PAGE_URL_PREFIX)
    page.save(update_fields=["url"])
  for page in CustomFlatPage.objects.filter(url__startswith="/pages/"):
    page.url = page.url.replace("/pages/", "/")
    page.save(update_fields=["url"])


def reverseMigrateAdminMessages(apps, schema_editor):
  CustomFlatPage = apps.get_model("pages", "FlatPage")
  for page in CustomFlatPage.objects.filter(url__startswith=settings.ADMIN_MESSAGE_PAGE_URL_PREFIX):
    page.url = page.url.replace(settings.ADMIN_MESSAGE_PAGE_URL_PREFIX, "/pages/admin-message")
    page.save(update_fields=["url"])
  for page in CustomFlatPage.objects.filter(url__startswith=settings.MENU_PAGE_URL_PREFIX):
    page.url = page.url.replace(settings.MENU_PAGE_URL_PREFIX, "")
    page.save(update_fields=["url"])


class Migration(migrations.Migration):
  dependencies = [
    ("pages", "0002_import_predefined_pages"),
  ]

  operations = [
    migrations.RunPython(migrateAdminMessages, reverse_code=reverseMigrateAdminMessages),
  ]
