from classified_ads.tests.factories import ClassifiedAdFactory
from core.tests.ui import PlaywrightTestCase
from members.tests.factories import MemberFactory


class ClassifiedAdsUITestBase(PlaywrightTestCase):
  """Base class for Classified Ads UI tests with pre-created test fixtures."""

  def setUp(self):
    super().setUp()

    # Create a test ad owned by the admin user (self.user)
    self.ad = ClassifiedAdFactory(
      title="Test Classified Ad",
      owner=self.user,
      category="home",
      subcategory="furniture",
      create_photos=False,
    )

    # Create multiple ads for list page tests
    self.ads = ClassifiedAdFactory.create_batch(
      5,
      owner=self.user,
      create_photos=False,
    )

    # Create a non-owner user for permission tests
    self.other_user = MemberFactory(
      username="otheruser",
      first_name="Other",
      last_name="User",
      birthdate="1995-05-15",
    )
    self.other_user.set_password("password")
    self.other_user.save()
