import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.cache import cache
from django.test import RequestFactory

from core.tests.ui import PlaywrightTestCase
from members.models import Member
from pages.services import seed_tenant_pages
from saas.services import create_tenant_request
from saas.tokens import TenantRequestTokenManager
from tenants.models import Tenant, TenantSettings

from ..utils import skip_if_saas_off

_PWD = "pw-12345-Aa"


class SaasUITestBase(PlaywrightTestCase):
  """Base for saas UI tests: skip when the SaaS flag is off, reset the throttle."""

  def setUp(self):
    # /saas/ URLs only exist when the flag is on at URLconf import time
    skip_if_saas_off(self)
    super().setUp()
    cache.clear()  # signup throttle state (5 requests/hour/IP)

  def make_tenant_request(self, email="founder@example.com", name="Smith"):
    return create_tenant_request(email=email, tenant_name=name)

  def validate_link_path(self, tenant_request):
    """Absolute signed link turned into a path usable with self.url()."""
    request = RequestFactory().get("/")
    link = TenantRequestTokenManager().generate_link(request, tenant_request)
    return link.replace("http://testserver", "")

  def make_tenant_admin(self, email="joe@example.com", password=True):
    """Tenant + settings + admin member ready to log in.

    username/email deliberately differ from the superuser created by
    PlaywrightTestCase.setUp() ("admin"/"admin@example.com").
    """
    tenant = Tenant.objects.create(name="Smith", slug="smith")
    TenantSettings.objects.create(tenant=tenant)
    # the home page includes the tenant's own copy of the predefined pages
    seed_tenant_pages(tenant)
    admin = Member.unscoped.create(
      username="joe",
      email=email,
      tenant=tenant,
      role=Member.Role.ADMIN,
      first_name="Joe",
      last_name="Smith",
    )
    if password:
      admin.set_password(_PWD)
    else:
      admin.set_unusable_password()
    admin.save()
    return tenant, admin
