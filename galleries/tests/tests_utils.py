from core.utils import test_media_root_decorator
from galleries.models import Gallery, Photo
from members.tests.tests_member_base import MemberTestCase
from tenants.models import Tenant
from tenants.scoping import set_current_tenant


@test_media_root_decorator(__file__)
class GalleryBaseTestCase(MemberTestCase):
  def setUp(self):
    super().setUp()
    # Gallery/Photo are TenantModel: activate the (default) tenant for direct ORM
    # creation in tests. View-based creation gets the tenant from the middleware
    # (the logged-in member lives on the default tenant).
    set_current_tenant(Tenant.get_default())

  def tearDown(self):
    # keep the tenant active so the scoped cleanup below sees the test rows
    set_current_tenant(Tenant.get_default())
    for gallery in Gallery.objects.filter(parent=None):
      gallery.delete()
    self.assertEqual(Gallery.objects.count(), 0)
    self.assertEqual(Photo.objects.count(), 0)
    set_current_tenant(None)
    super().tearDown()
