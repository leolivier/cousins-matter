from django.urls import reverse
from django.contrib.flatpages.models import FlatPage

from pages.utils import flatpage_url


class BasePageTestCase():

  def setUp(self):
    super().setUp()
    self.page_data = {
      'url': '/a-level/a-slug/',
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
    self.assertRedirects(response, flatpage_url(page_data['url']), 302, 200)
    self.assertTemplateUsed(response, 'flatpages/default.html')
    page = FlatPage.objects.get(url=page_data['url'])
    self.assertIsNotNone(page)
    self.assertEqual(page_data['url'], page.url)
    self.assertContains(response, f'''<div class="container px-2">
{page_data['content']}
</div>''', html=True)
    return page
