from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from members.tests.tests_member import MemberTestCase
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext as _, override as lang_override
from members.tests.tests_birthdays import TestBirthdaysMixin
from .forms import PageForm


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


class TestDisplayPageMenu(TestPageMixin, BasePageTestCase, MemberTestCase):
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
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    self.assertEqual(response.status_code, 200)
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
    bad_page_data = {
        'url': f'{self.pages_prefix}1rst-title/',  # doesn't start with /pages/publish=>won't appear in the navbar
        'title': 'first title',
        'content': 'first content',
      }

    bad_page = self._test_create_page(bad_page_data)
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    # print("response", response)
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, f'''
<a class="navbar-item" href="{bad_page.url}">
  <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
  {bad_page.title}
</a>''', html=True)


class TestHomePageMixin(TestPageMixin):
  def setUp(self):
    super().setUp()
    # create home pages in the database
    base_content = "<p class='content'>a wonderful content for an home page with an image: <img src='/data/my-image.png'></p>"
    self.home_pages = {}
    for lang in ['fr-FR', 'en-US']:
      self.home_pages[lang] = {}
      for kind in ['authenticated', 'unauthenticated']:
        content = f'{base_content} <p>language code={lang} and auth={kind}</p>'
        self.home_pages[lang][kind] = FlatPage.objects.create(
          url=f'/pages/{lang}/home/{kind}/',
          title='a home page',
          content=content
        )

  def check_home_page(self, lang, auth):
    with lang_override(lang):
      with override_settings(LANGUAGE_CODE=lang):
        response = self.client.get(reverse('cm_main:Home'), follow=True)
        # print(response.content.decode().replace('\\t', '\t').replace('\\n', '\n'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.home_pages[lang][auth].content, html=True)
        return response


class TestAuthenticatedHomePage(TestHomePageMixin, TestBirthdaysMixin, BasePageTestCase, MemberTestCase):

  @override_settings(INCLUDE_BIRTHDAYS_IN_HOMEPAGE=False)
  def test_home_page_without_birthdays(self):
    for lang in ['fr-FR', 'en-US']:
      response = self.check_home_page(lang, "authenticated")
      with lang_override(lang):
        if (self.member and self.member.birthdate):
          self.check_birthday_today(self.member, response, reversed=True)
        else:
          self.check_no_birthdays(response, reversed=True)

  @override_settings(INCLUDE_BIRTHDAYS_IN_HOMEPAGE=True)
  def test_home_page_with_birthdays(self):
    for lang in ['fr-FR', 'en-US']:
      response = self.check_home_page(lang, "authenticated")
      with lang_override(lang):
        if (self.member and self.member.birthdate):
          self.check_birthday_today(self.member, response)
        else:
          self.check_no_birthdays(response)


class TestUnAuthenticatedHomePage(TestHomePageMixin, BasePageTestCase, TestCase):

  def test_unauthenticated_home_page(self):
    for lang in ['fr-FR', 'en-US']:
      self.check_home_page(lang, "unauthenticated")
