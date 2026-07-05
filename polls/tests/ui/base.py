from django.utils import timezone

from core.tests.ui import PlaywrightTestCase
from polls.tests.factories import PollFactory


class PollsUITestBase(PlaywrightTestCase):
  """Base class for Polls UI tests with pre-created test fixtures."""

  def setUp(self):
    super().setUp()

    # Create test polls owned by the admin user (suppress auto-questions)
    self.poll1 = PollFactory(
      owner=self.user,
      title="Sondage sur le prochain repas",
      description="Quel repas devrions-nous organiser ?",
      pub_date=timezone.now(),
      create_questions=False,
    )
    self.poll2 = PollFactory(
      owner=self.user,
      title="Choix du lieu de vacances",
      description="Où devrions-nous partir l'été prochain ?",
      pub_date=timezone.now(),
      create_questions=False,
    )
    self.poll3 = PollFactory(
      owner=self.user,
      title="Sondage fermé",
      description="Ce sondage est déjà terminé.",
      pub_date=timezone.now(),
      create_questions=False,
    )
