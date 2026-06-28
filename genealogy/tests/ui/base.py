from core.tests.ui import PlaywrightTestCase
from genealogy.tests.factories import FamilyFactory, PersonFactory


class GenealogyUITestBase(PlaywrightTestCase):
  """Base class for Genealogy UI tests with pre-created test fixtures."""

  def setUp(self):
    super().setUp()

    # Create people without linking to members (member=None) to keep tests fast
    self.person1 = PersonFactory(
      first_name="Jean",
      last_name="Dupont",
      sex="M",
      member=None,
    )
    self.person2 = PersonFactory(
      first_name="Marie",
      last_name="Dupont",
      sex="F",
      member=None,
    )
    self.person3 = PersonFactory(
      first_name="Pierre",
      last_name="Martin",
      sex="M",
      member=None,
    )

    # Create a family without children to keep tests fast
    self.family = FamilyFactory(
      partner1=self.person1,
      partner2=self.person2,
      union_type="MARR",
      create_children=False,
    )

    # Create additional people for list pagination
    self.extra_people = PersonFactory.create_batch(
      5,
      member=None,
    )
