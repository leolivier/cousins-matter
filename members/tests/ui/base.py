import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from core.tests.ui import PlaywrightTestCase
from members.tests.factories import MemberFactory


class MembersUITestBase(PlaywrightTestCase):
  """Base class for Members UI tests with pre-created test members."""

  def setUp(self):
    super().setUp()
    # self.user is already created by PlaywrightTestCase (admin superuser)
    # Create test members
    self.member1 = MemberFactory(
      first_name="Alice",
      last_name="Dupont",
      is_active=True,
    )
    self.member2 = MemberFactory(
      first_name="Bob",
      last_name="Martin",
      is_active=True,
    )
    self.member3 = MemberFactory(
      first_name="Charlie",
      last_name="Durand",
      is_active=False,
    )
