from django.utils.html import escape
from django.conf import settings
from django.urls import reverse
from members.tests.tests_member import MemberTestCase
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext as _
from .forms import PageForm


class TestPage(MemberTestCase):
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


class TestCreatePage(TestPage):
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
    self._test_create_page({
        'url': f'{self.pages_prefix}/2nd-title/',
        'title': '2nd title',
        'content': '2nd content',
      })
    response = self.client.post(reverse("pages-edit:create"), {
        'url': f'{self.pages_prefix}/2nd-title/3rd-title/',
        'title': '3rd title',
        'content': '3rd content',
      }, follow=True)

    self.print_response(response)
    self.assertContains(response, f'''
<ul class="errorlist"><li>
      {_("A flatpage cannot be a subpage of another flatpage, check your URLs")}
</li></ul>''', html=True)

  def test_same_url(self):
    # first create one page
    self._test_create_page()
    # then try to create another one with the same url
    new_page_data = {
      'url': self.page_data['url'],
      'title': 'another title',
      'content': 'another content',
    }
    response = self.client.post(reverse("pages-edit:create"), new_page_data, follow=True)
    # self.print_response(response)
    error_message = escape(_("Flatpage with url %(url)s already exists") % {'url': new_page_data['url']})
    self.assertContains(response, f'<ul class="errorlist"><li>{error_message}</li></ul>', html=True)


class TestUpdatePage(TestPage):
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
    response = self.client.post(reverse("pages-edit:update", args=[page2.url]), new_page_data, follow=True)
    # self.print_response(response)
    error_message = escape(_("Flatpage with url %(url)s already exists") % {'url': new_page_data['url']})
    self.assertContains(response, f'<ul class="errorlist"><li>{error_message}</li></ul>', html=True)


class TestDisplayPageList(TestPage):
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


class TestDisplayPageMenu(TestPage):
  def test_display_page_menu(self):
    page_list_data = [
      {
        'url': f'{self.pages_prefix}publish/1rst-title/',
        'title': 'first title',
        'content': 'first content',
      },
      {
        'url': f'{self.pages_prefix}publish/level/2nd-title/',
        'title': '2nd title',
        'content': '2nd content',
      },
      {
        'url': f'{self.pages_prefix}publish/level/3rd-title/',
        'title': '3rd title',
        'content': '3rd content',
      }
    ]
    pages = [self._test_create_page(page_data) for page_data in page_list_data]
    response = self.client.get(reverse('cm_main:Home'))
    self.assertContains(response, f'''
<a class="navbar-item" href="{pages[0].url}">
  <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
  {pages[0].title}
</a>''', html=True)
    self.assertContains(response, f'''
<div class="navbar-item has-dropdown is-hoverable">
  <p class="navbar-link">
    <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next"></i></span>
    level
  </p>
  <div class="navbar-dropdown is-right">
    <a class="navbar-item" href="{pages[1].url}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
      {pages[1].title}
    </a>
    <a class="navbar-item" href="{pages[2].url}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
      {pages[2].title}
    </a>
  </div>
</div>''', html=True)

  def test_display_bad_page_menu(self):
    bad_page_list_data = [
      {
        'url': f'{self.pages_prefix}1rst-title/',  # doesn't start with /pages/publish=>won't appear in the navbar
        'title': 'first title',
        'content': 'first content',
      },
    ]
    pages = [self._test_create_page(page_data) for page_data in bad_page_list_data]
    response = self.client.get(reverse('cm_main:Home'))
    self.assertNotContains(response, f'''
<a class="navbar-item" href="{pages[0].url}">
  <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
  {pages[0].title}
</a>''', html=True)
