import os
import shutil
from django.conf import settings
from django.urls import reverse
from django.test import TestCase
from django.templatetags.static import static

from cousinsmatter.context_processors import override_settings


class TestSiteLogo(TestCase):
  fixtures = ['init-pages.json']

  def test_custom_logo(self):
    """test the site logo"""
    logo_basefilename = 'test-logo.jpg'
    logo_full_path = os.path.join(settings.MEDIA_ROOT, 'public', logo_basefilename)
    logo_testresources_file = os.path.join(os.path.dirname(__file__), 'resources', logo_basefilename)
    logo_url = f'{settings.PUBLIC_MEDIA_URL}{logo_basefilename}'

    current_logo_url = static(settings.SITE_LOGO)
    format = '''<a class="navbar-item" href="/">
  <img src="%s" width="112" height="28">
</a>'''
    # check if the current logo is already set to the test logo
    if current_logo_url == logo_url:
      self.assertTrue(False, f'SITE_LOGO should not be set to {logo_url} for this test')
    else:
      # test the current_logo
      response = self.client.get(reverse('cm_main:Home'), follow=True)
      self.assertContains(response, format % current_logo_url, html=True)

    # if the file doesn't exist, copy it from resources
    if (not os.path.isfile(logo_full_path)):
      # Make sure the destination directory exists
      os.makedirs(os.path.dirname(logo_full_path), exist_ok=True)
      # Copy the test resource
      shutil.copy2(logo_testresources_file, logo_full_path)

    # override the settings SITE_LOGO
    with override_settings(SITE_LOGO=logo_url):
      response = self.client.get(reverse('cm_main:Home'), follow=True)
      self.assertContains(response, format % logo_url, html=True)

    # clean up
    if (os.path.isfile(logo_full_path)):
      os.remove(logo_full_path)
