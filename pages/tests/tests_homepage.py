from datetime import date, timedelta
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override as lang_override

from cousinsmatter.context_processors import override_settings
from members.models import Member
from members.tests.tests_member_base import MemberTestCase
from members.tests.tests_birthdays import TestBirthdaysMixin
from ..models import create_page, FlatPage
from .test_base import BasePageTestCase, TestPageMixin


class TestHomePageMixin(TestPageMixin):
  def setUp(self):
    super().setUp()
    # create home pages in the database
    base_content = "<p class='content'>a wonderful content for an home page with an image: <img src='/data/my-image.png'></p>"
    self.home_pages = {}
    for lang in ['fr', 'en-us']:
      self.home_pages[lang] = {}
      for kind in ['authenticated', 'unauthenticated']:
        url = f'/{lang}/home/{kind}/'
        # first, remove the one created by the fixture in other classes
        FlatPage.objects.filter(url=url).delete()
        # then create the new one
        content = f'{base_content} <p>language code={lang} and auth={kind}</p>'
        self.home_pages[lang][kind] = create_page(
          url=url,
          title='a home page',
          content=content
        )

  def check_home_page(self, lang, auth):
    with lang_override(lang):
      with override_settings(LANGUAGE_CODE=lang):
        response = self.client.get(reverse('cm_main:Home'), follow=True)
        # self.print_response(response)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.home_pages[lang][auth].content, html=True)
        return response


class TestAuthenticatedHomePage(TestHomePageMixin, TestBirthdaysMixin, BasePageTestCase, MemberTestCase):
  def check_if_birthdays(self, response, reversed=False):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    members = Member.objects.filter(birthdate__isnull=False)
    # print(f"\nchecking birthdays with include={settings.INCLUDE_BIRTHDAYS_IN_HOMEPAGE} "
    #       f"reversed={reversed} and lang={settings.LANGUAGE_CODE} "
    #       "for response:")
    # self.print_response(response)
    if members.count() > 0:
      for member in members:
        next_birthday = member.next_birthday
        # print("checking member", member.full_name, "next birthday", next_birthday, end=' ')
        if next_birthday == date.today():
          # print(f"should {'not' if reversed else ''} be today")
          self.check_birthday_today(member, response, reversed)
        elif next_birthday == tomorrow:
          # print(f"should {'not' if reversed else ''} be tomorrow")
          self.check_birthdays_tomorrow(member, response, reversed)
        elif next_birthday < today + timedelta(days=settings.BIRTHDAY_DAYS):
          # print(f"should {'not' if reversed else ''} be after tomorrow")
          self.check_birthdays_after_tomorrow(member, response, reversed)
        else:
          # print("should never be printed (too late)")
          pass
    else:
      self.check_no_birthdays(response, reversed)

  @override_settings(INCLUDE_BIRTHDAYS_IN_HOMEPAGE=False)
  def test_home_page_without_birthdays(self):
    for lang in ['fr', 'en-us']:
      with lang_override(lang):
        response = self.check_home_page(lang, "authenticated")
        self.check_if_birthdays(response, reversed=True)

  @override_settings(INCLUDE_BIRTHDAYS_IN_HOMEPAGE=True)
  def test_home_page_with_birthdays(self):
    for lang in ['fr', 'en-us']:
      with lang_override(lang):
        response = self.check_home_page(lang, "authenticated")
        self.check_if_birthdays(response)


class TestUnAuthenticatedHomePage(TestHomePageMixin, BasePageTestCase, TestCase):

  def test_unauthenticated_home_page(self):
    for lang in ['fr', 'en-us']:
      self.check_home_page(lang, "unauthenticated")
