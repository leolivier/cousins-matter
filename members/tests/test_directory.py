from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.urls import reverse

from core.utils import test_media_root_decorator, test_resource_full_path
from core.tests import test_site_logo
from tenants.models import TenantSettings
from tenants.scoping import tenant_context
from tenants.settings_overrides import clear_tenant_settings_cache

from .tests_member_base import MemberTestCase
from ..views.views_directory import MembersDirectoryView, MembersPrintDirectoryView


class TestMemberDirectory(MemberTestCase):
  def setUp(self):
    """Initializes test data for member directory."""
    super().setUp()
    for _ in range(4):
      self.create_member()

  def test_member_directory(self):
    """Tests that the member directory displays correctly with all visible members."""
    response = self.client.get(reverse("members:directory"), follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, MembersDirectoryView)
    self.assertTemplateUsed(response, "members/members/members_directory.html")
    for member in self.created_members:
      member_link = f"""
        <a class="button is-link is-light" href="{reverse("members:detail", args=[member.username])}">
          <strong>{member.full_name}</strong>
        </a>
        """
      self.assertContains(response, member_link, html=True)

  def test_pdf_generation(self):
    """Tests that PDF generation for the member directory works correctly."""
    response = self.client.get(reverse("members:print_directory"), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, MembersPrintDirectoryView)
    self.assertIs(response.__class__, FileResponse)
    self.assertEqual(response["Content-Type"], "application/pdf")


@test_media_root_decorator(__file__)
class TestDirectoryPDFWithUploadedLogo(MemberTestCase):
  def tearDown(self):
    # tenant_setting memoizes per tenant pk — drop the logo override from the
    # cache so later test classes fall back to the global default
    clear_tenant_settings_cache()
    super().tearDown()

  def test_pdf_with_uploaded_public_logo(self):
    """An uploaded per-tenant logo (public-media URL) resolves to a disk path for FPDF."""
    from django.core.files.storage import FileSystemStorage

    from ..services.directory import DirectoryPDF

    storage = FileSystemStorage(location=Path(settings.MEDIA_ROOT) / "public")
    with open(test_resource_full_path("test-logo.jpg", test_site_logo.__file__), "rb") as f:
      storage.save("logos/default.jpg", ContentFile(f.read()))
    TenantSettings.objects.update_or_create(
      tenant=self.member.tenant,
      defaults={"overrides": {"site_logo": f"{settings.PUBLIC_MEDIA_URL}logos/default.jpg"}},
    )
    clear_tenant_settings_cache()
    with tenant_context(self.member.tenant):
      pdf = DirectoryPDF("P", "mm", "A4")
      data = pdf.output(dest="S")  # same call as the print view; without dest, fpdf 1.7 prints to stdout
    self.assertTrue(data)
