from django.forms import ValidationError
from django.urls import reverse
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext as _

from pages.utils import flatpage_url


class BasePageTestCase():

  def setUp(self):
    super().setUp()
    self.page_data = {
      'url': '/a-level/a-slug/',
      'title': 'a title',
      'content': 'a content',
      'save': 'true',  # change to save-and-continue to test this mode
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
    if 'save-and-continue' in page_data:
      self.assertTemplateUsed(response, "pages/page_form.html")  # remain on edit page
      self.assertContainsMessage(response, 'success', _("Page \"%(title)s\" saved") % {"title": page_data['title']})
    elif 'save' in page_data:
      self.assertRedirects(response, flatpage_url(page_data['url']), 302, 200)
      self.assertTemplateUsed(response, 'flatpages/default.html')
    else:
      raise ValidationError('no save or save-and-continue in page_data')
    page = FlatPage.objects.get(url=page_data['url'])
    self.assertIsNotNone(page)
    self.assertEqual(page_data['url'], page.url)
    content = f'''<div class="control">
    <textarea name="content" cols="40" rows="10" class="richtextarea" id="id_content">
{page_data['content']}
    </textarea>
  </div>''' if 'save-and-continue' in page_data else f'''<div class="container px-2">
{page_data['content']}
</div>''' if 'save' in page_data else 'ERROR! no save or save-and-continue in page_data'
    self.assertContains(response, content, html=True)
    return page
