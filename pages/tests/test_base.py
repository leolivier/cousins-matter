from django.conf import settings
from django.urls import reverse
from django.contrib.flatpages.models import FlatPage


class BasePageTestCase():
  pages_prefix = f'/{settings.PAGES_URL_PREFIX}/'

  def setUp(self):
    super().setUp()
    self.page_data = {
      'url': f'{self.pages_prefix}a-title/',
      'title': 'a title',
      'content': 'a content',
    }

  def tearDown(self):
    FlatPage.objects.all().delete()
    super().tearDown()


class TestPageMixin():
  def _test_create_page(self, page_data=None, prresp=False):
    if page_data is None:
      page_data = self.page_data
    # print('creating page', page_data['url'], page_data['title'])
    response = self.client.post(reverse("pages-edit:create"), page_data, follow=True)
    if prresp:
      self.print_response(response)
    self.assertEqual(response.status_code, 200)
    page = FlatPage.objects.get(url=page_data['url'])
    self.assertIsNotNone(page)
    self.assertEqual(page_data['url'], page.url)
    return page
