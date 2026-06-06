import os
from unittest.mock import patch

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.contrib.auth import get_user_model

from core.tests.ui import PlaywrightTestCase
from troves.tests.factories import TroveFactory


class TroveUITestBase(PlaywrightTestCase):
  """Base class for Troves UI tests using Playwright."""

  def setUp(self):
    super().setUp()
    self.user = get_user_model().objects.create_superuser(
      "admin",
      "admin@example.com",
      "password",
      first_name="Admin",
      last_name="User",
      birthdate="2000-01-01",
    )
    # patch create_thumbnail to avoid the Trove.save() → thumbnail failure →
    # self.delete() → raises ValidationError → no-id bug.
    with patch("troves.models.create_thumbnail") as mock_thumbnail:
      self.troves = [
        TroveFactory(category="history", owner=self.user),
        TroveFactory(category="recipes", owner=self.user),
        TroveFactory(category="arts", owner=self.user),
      ]
      # make the mock return the picture itself (a no-op thumbnail)
      mock_thumbnail.side_effect = lambda image, size: image

    # errors tracking
    self.errors: list[str] = []
    self.page.on("pageerror", lambda err: self.errors.append(str(err)))
    self.page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
