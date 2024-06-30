from django.conf import settings
from django.urls import reverse
from members.tests.tests_member_base import MemberTestCase
from django.utils.translation import gettext as _
from ..forms import PageForm
from .test_base import BasePageTestCase, TestPageMixin


class TestCreatePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_create_page(self):
    response = self.client.get(reverse("pages-edit:create"))
    self.assertTemplateUsed(response, "pages/page_form.html")

    self._test_create_page()

  def test_url_checks(self):
    page_data = self.page_data.copy()
    page_data['url'] = f'/no{settings.PAGES_URL_PREFIX}/something'
    form = PageForm(page_data)
    self.assertFormError(form, 'url', [_(f"URLs MUST start with {self.pages_prefix}")])
    page_data['url'] = f'{self.pages_prefix}something'
    form = PageForm(page_data)
    self.assertFormError(form, 'url', [_("URL is missing a trailing slash.")])
    page_data['url'] = f'{self.pages_prefix}'
    form = PageForm(page_data)
    self.assertFormError(form, 'url', [_(f"URLs cannot be only {self.pages_prefix}, please add some path behind")])
    page_data['url'] = f'{self.pages_prefix}wrong-chars!#()'
    form = PageForm(page_data)
    self.assertFormError(form, 'url', [_(
                "This value must contain only letters, numbers, dots, "
                "underscores, dashes, slashes or tildes."
            )])

  def test_url_checks_with_other_pages(self):
    # first create one page
    self._test_create_page()
    # then try to create another one with the same url
    new_page_data = {
      'url': self.page_data['url'],
      'title': 'another title',
      'content': 'another content',
    }
    form = PageForm(new_page_data)
    self.assertFormError(form, 'url', [_("Flatpage with url %(url)s already exists") % {'url': new_page_data['url']}])
    # now, try to create with "sub url"
    url = self.page_data['url']
    form = PageForm({
        'url': f'{url}/3rd-title/',
        'title': '3rd title',
        'content': '3rd content',
      })
    self.assertFormError(form, 'url', [_("A flatpage cannot be a subpage of another flatpage, check your URLs")])


class TestUpdatePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_update_page(self):
    # first create it
    page = self._test_create_page()
    # now try to update it
    new_page_data = {
      'url': f'{self.pages_prefix}another-title/',
      'title': 'another title',
      'content': 'another content',
    }
    response = self.client.post(reverse("pages-edit:update", args=[page.url]), new_page_data, follow=True)
    self.assertEqual(response.status_code, 200)
    page.refresh_from_db()
    self.assertEqual(page.url, new_page_data['url'])
    self.assertEqual(page.title, new_page_data['title'])
    self.assertEqual(page.content, new_page_data['content'])

  def test_same_url(self):
    # first create 2 pages with different urls
    page1 = self._test_create_page()
    # 2nd page
    new_page_data = {
      'url': f'{self.pages_prefix}another-title/',
      'title': 'another title',
      'content': 'another content',
    }
    page2 = self._test_create_page(new_page_data)

    # Now try to update page 2 with the same url with the same URL as page1
    new_page_data['url'] = page1.url
    new_page_data['id'] = page2.id
    form = PageForm(new_page_data)
    self.assertFormError(form, 'url', [_("Flatpage with url %(url)s already exists") % {'url': new_page_data['url']}])


class TestDisplayPageList(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_display_page(self):
    # first create 2 pages with different urls
    page1 = self._test_create_page()
    # 2nd page
    new_page_data = {
      'url': f'{self.pages_prefix}another-title/',
      'title': 'another title',
      'content': 'another content',
    }
    page2 = self._test_create_page(new_page_data)
    # now, display them
    response = self.client.get(reverse("pages-edit:list"))
    self.assertEqual(response.status_code, 200)
    for page in [page1, page2]:
      self.assertContains(response, f'''
  <div class="panel-block">
    <a href="{reverse('pages-edit:update', args=[page.url])}">
      <span class="panel-icon">
        <i class="mdi mdi-24px mdi-page-next" aria-hidden="true"></i>
      </span>
      {page.title}
    </a>
  </div>''', html=True)
