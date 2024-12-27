from datetime import date, timedelta
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override as lang_override

from cousinsmatter.context_processors import override_settings
from members.models import Member
from members.tests.tests_member_base import MemberTestCase
from members.tests.tests_birthdays import TestBirthdaysMixin
from ..models import FlatPage
from .test_base import BasePageTestCase, TestPageMixin


class TestHomePageMixin(TestPageMixin):

  def check_home_page(self, lang, auth):
    home_url = '/' + lang + '/home/' + auth + '/'
    # print("home_url", home_url)
    # print("urls home page", {page.url for page in FlatPage.objects.filter(predefined=True)})
    home_content = FlatPage.objects.get(url__iexact=home_url).content
    with lang_override(lang):
      with override_settings(LANGUAGE_CODE=lang):
        response = self.client.get(reverse('cm_main:Home'), follow=True)
        # self.print_response(response)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, home_content, html=True)
        # print("home ok")
        return response


class TestAuthenticatedHomePage(TestHomePageMixin, TestBirthdaysMixin, BasePageTestCase, MemberTestCase):
  def check_if_birthdays(self, response, reversed=False):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    members = Member.objects.filter(birthdate__isnull=False)
    # print(f"\nchecking birthdays with include={settings.INCLUDE_BIRTHDAYS_IN_HOMEPAGE} "
    #       f"reversed={reversed} and lang={get_language()} "
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
    for lang in ['fr', 'en-US']:
      with lang_override(lang):
        response = self.check_home_page(lang, "authenticated")
        self.check_if_birthdays(response, reversed=True)

  @override_settings(INCLUDE_BIRTHDAYS_IN_HOMEPAGE=True)
  def test_home_page_with_birthdays(self):
    for lang in ['fr', 'en-US']:
      with lang_override(lang):
        response = self.check_home_page(lang, "authenticated")
        self.check_if_birthdays(response)


class TestUnAuthenticatedHomePage(TestHomePageMixin, BasePageTestCase, TestCase):

  def test_unauthenticated_home_page(self):
    for lang in ['fr', 'en-US']:
      self.check_home_page(lang, "unauthenticated")
