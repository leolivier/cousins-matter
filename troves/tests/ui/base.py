from unittest.mock import patch

from core.tests.ui import PlaywrightTestCase
from troves.tests.factories import TroveFactory


class TroveUITestBase(PlaywrightTestCase):
  """Base class for Troves UI tests using Playwright."""

  def setUp(self):
    super().setUp()
    # patch create_thumbnail to avoid the Trove.save() → thumbnail failure →
    # self.delete() → raises ValidationError → no-id bug.
    with patch("troves.models.create_thumbnail") as mock_thumbnail:
      # make the mock return the picture itself (a no-op thumbnail)
      # doit être défini AVANT la création des Trove, sinon le MagicMock
      # par défaut est assigné à .thumbnail et provoque une FieldError
      # au moment du save(update_fields=["thumbnail"])
      mock_thumbnail.side_effect = lambda image, size: image
      self.troves = [
        TroveFactory(category="history", owner=self.user),
        TroveFactory(category="recipes", owner=self.user),
        TroveFactory(category="arts", owner=self.user),
      ]
