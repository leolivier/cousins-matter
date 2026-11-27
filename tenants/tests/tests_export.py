"""Tenant data export: request, build, email and (expiring) download.

Runs with MULTI_TENANT_ENABLED=True (like the rest of the tenants suite);
skipped otherwise because the /tenants/ URLs are not mounted then.
"""

import io
import zipfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from core.tests.test_django_q import django_q_sync_class
from core.utils import test_media_root_decorator
from tenants.models import Tenant, TenantExport, TenantSettings
from tenants.scoping import set_current_tenant, tenant_context
from tenants.settings_overrides import clear_tenant_settings_cache

Member = get_user_model()

_PWD = "pw-12345-Aa"


def _skip_if_off(testcase):
  if not settings.MULTI_TENANT_ENABLED:
    testcase.skipTest("MULTI_TENANT_ENABLED is off in this environment")


def _make_member(tenant, username, role=Member.Role.MEMBER):
  with tenant_context(tenant):
    return Member.objects.create_member(
      username=username,
      password=_PWD,
      email=f"{username}@example.com",
      first_name=username,
      last_name="x",
      is_active=True,
      role=role,
      privacy_consent=True,
    )


@override_settings(LANGUAGE_CODE="en")
@test_media_root_decorator(__file__)
class TenantExportTests(TestCase):
  def setUp(self):
    _skip_if_off(self)
    set_current_tenant(None)
    # a rolled-back TenantSettings row leaves its memoized overrides behind
    clear_tenant_settings_cache()
    self.tenant = Tenant.objects.create(name="Smith", slug="smith")
    self.other = Tenant.objects.create(name="Other", slug="other")
    self.admin = _make_member(self.tenant, "smith-admin", Member.Role.ADMIN)
    self.member = _make_member(self.tenant, "smith-member")
    self.other_member = _make_member(self.other, "other-member")

  def tearDown(self):
    set_current_tenant(None)

  def _build(self):
    """Run the worker task synchronously on the main tenant."""
    export = TenantExport.unscoped.create(tenant=self.tenant, created_by=self.admin)
    from tenants.tasks import build_tenant_export

    build_tenant_export(export.pk)
    return TenantExport.unscoped.get(pk=export.pk)

  def _ready_export(self):
    export = TenantExport.unscoped.create(
      tenant=self.tenant,
      created_by=self.admin,
      status=TenantExport.Status.READY,
      expires_at=timezone.now() + timedelta(days=7),
    )
    export.file.save(f"{export.token}.zip", ContentFile(b"PK-fake-zip"), save=True)
    return export

  def _zip_names(self, export):
    with zipfile.ZipFile(io.BytesIO(export.file.read())) as archive:
      return archive.namelist()

  def test_non_admin_cannot_request_export(self):
    self.client.force_login(self.member)
    response = self.client.post(reverse("tenants:export_create"))
    self.assertEqual(response.status_code, 403)
    self.assertFalse(TenantExport.unscoped.exists())

  @django_q_sync_class
  def test_admin_request_builds_zip_and_emails_link(self):
    default_storage.save("smith/galleries/photo.jpg", ContentFile(b"jpg"))
    default_storage.save("other/galleries/secret.jpg", ContentFile(b"jpg"))
    self.client.force_login(self.admin)

    response = self.client.post(reverse("tenants:export_create"))

    self.assertRedirects(response, reverse("tenants:settings"))
    export = TenantExport.unscoped.get()
    self.assertEqual(export.status, TenantExport.Status.READY)
    self.assertIsNotNone(export.expires_at)

    names = self._zip_names(export)
    self.assertIn("export.xlsx", names)
    self.assertIn("media/galleries/photo.jpg", names)
    self.assertNotIn("media/galleries/secret.jpg", names)

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, [self.admin.email])
    self.assertIn(str(export.token), mail.outbox[0].body)
    self.assertIn(export.expires_at.date().isoformat(), mail.outbox[0].body)

  def test_workbook_has_one_sheet_per_model_with_tenant_rows_only(self):
    default_storage.save("smith/galleries/photo.jpg", ContentFile(b"jpg"))
    export = self._build()

    with zipfile.ZipFile(io.BytesIO(export.file.read())) as archive:
      workbook = load_workbook(io.BytesIO(archive.read("export.xlsx")))

    sheet = workbook["members"]
    # header + the two members of this tenant; the other tenant's member is absent
    self.assertEqual(sheet.max_row, 3)
    values = [cell.value for row in sheet.iter_rows() for cell in row]
    self.assertIn("smith-admin", values)
    self.assertNotIn("other-member", values)
    # the tenant column and password hashes never leave the server
    headers = [cell.value for cell in sheet[1]]
    self.assertNotIn("Tenant", headers)
    self.assertNotIn("Password", headers)

  def test_headers_use_the_tenant_language(self):
    TenantSettings.objects.create(tenant=self.tenant, overrides={"language_code": "fr"})
    export = self._build()

    with zipfile.ZipFile(io.BytesIO(export.file.read())) as archive:
      workbook = load_workbook(io.BytesIO(archive.read("export.xlsx")))

    headers = [cell.value for cell in workbook["membres"][1]]
    self.assertIn("prénom", headers)

  def test_any_tenant_member_can_download(self):
    export = self._ready_export()
    self.client.force_login(self.member)
    response = self.client.get(reverse("tenants:export_download", args=[export.token]))
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Content-Type"], "application/zip")
    self.assertIn("attachment", response["Content-Disposition"])

  def test_other_tenant_member_gets_404(self):
    export = self._ready_export()
    self.client.force_login(self.other_member)
    response = self.client.get(reverse("tenants:export_download", args=[export.token]))
    self.assertEqual(response.status_code, 404)

  def test_anonymous_is_redirected_to_login(self):
    export = self._ready_export()
    response = self.client.get(reverse("tenants:export_download", args=[export.token]))
    self.assertEqual(response.status_code, 302)
    self.assertIn(reverse("members:login"), response["Location"])

  def test_expired_export_is_deleted(self):
    export = self._ready_export()
    export.expires_at = timezone.now() - timedelta(days=1)
    export.save(update_fields=["expires_at"])
    self.client.force_login(self.member)

    response = self.client.get(reverse("tenants:export_download", args=[export.token]))

    self.assertEqual(response.status_code, 404)
    self.assertFalse(TenantExport.unscoped.filter(pk=export.pk).exists())
