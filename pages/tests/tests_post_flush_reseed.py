"""The predefined pages must survive TransactionTestCase.flush.

flush wipes every table but leaves django_migrations untouched, so the
pages.0002 seeding migration never reruns on a reused (``--keepdb``) test
database. The re-seed happens through the signal chain instead: flush emits
post_migrate, ``tenants.models._seed_tenants_post_migrate`` re-creates the
default tenant, and its creation fires the ``pages.apps`` post_save hook
``seed_pages_on_tenant_create`` which re-seeds the predefined pages
(idempotently). Without that chain, any later keepdb run on such a database
fails with "page not found for url=/en/home/authenticated/".
"""

from django.core.management import call_command
from django.test import TransactionTestCase

from ..models import FlatPage


class PostFlushReseedTests(TransactionTestCase):
  def test_flush_reseeds_predefined_pages(self):
    self.assertTrue(FlatPage.unscoped.filter(predefined=True).exists())
    FlatPage.unscoped.all().delete()
    self.assertFalse(FlatPage.unscoped.filter(predefined=True).exists())
    # flush wipes everything and emits post_migrate, which must re-seed
    call_command("flush", interactive=False, verbosity=0)
    self.assertTrue(
      FlatPage.unscoped.filter(predefined=True).exists(),
      "predefined pages must be re-seeded after a flush",
    )
