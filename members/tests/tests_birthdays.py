from datetime import date, timedelta

from django.conf import settings
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.translation import gettext as _

from cm_main.templatetags.cm_tags import icon
from .tests_member_base import MemberTestCase, get_new_member_data


class TestBirthdaysMixin:
  def get_member_with_bday(self, bday):
    # create a member with birthday = bday
    new_data = get_new_member_data(birthdate=bday)
    return self.create_member(new_data)

  def check_birthday(
    self,
    member,
    color,
    expected_chain,
    with_icons=False,
    response=None,
    reversed=False,
  ):
    response = response or self.client.get(reverse("members:birthdays"))
    # self.print_response(response)
    common_chain = f"""<div class="cell has-background-{color}-light ml-2 pl-2 pr-1 is-flex
        is-align-items-center is-justify-content-right">
      <a href="/members/{member.id}/" class="has-text-{color}">{member.full_name}</a>
  </div>"""
    tester = self.assertNotContains if reversed else self.assertContains
    tester(response, common_chain, html=True)

    icons = f"""{icon("birthday")}{icon("birthday-variant")}{icon("birthday")}""" if with_icons else ""
    expected_chain = f"""
<div class="cell has-background-{color}-light mr-2 pl-1 pr-2 has-text-{color}">
{expected_chain}
{icons}
</div>"""
    tester(response, expected_chain, html=True)

  def check_birthday_today(self, member, response=None, reversed=False):
    b_is_today = _("turns %(age)s today, happy birthday!") % {"age": member.age}
    self.check_birthday(
      member,
      "danger",
      b_is_today,
      with_icons=True,
      response=response,
      reversed=reversed,
    )

  def check_birthdays_tomorrow(self, member, response=None, reversed=False):
    b_is_tomorrow = _("will turn %(age)s tomorrow, happy birthday!") % {"age": member.age + 1}
    self.check_birthday(
      member,
      "warning",
      b_is_tomorrow,
      with_icons=True,
      response=response,
      reversed=reversed,
    )

  def check_birthdays_after_tomorrow(self, member, response=None, reversed=False):
    b_date = date_format(member.next_birthday, "l d F", use_l10n=True)
    b_is_after = _("will turn %(age)s on %(birthday)s") % {
      "age": member.age + 1,
      "birthday": b_date,
    }
    self.check_birthday(
      member,
      "link",
      b_is_after,
      with_icons=False,
      response=response,
      reversed=reversed,
    )

  def check_no_birthdays(self, response=None, reversed=False):
    no_bdays = f"""
  <div>
    <p>{_("No birthdays in next %(ndays)s days") % {"ndays": settings.BIRTHDAY_DAYS}}.</p>
  </div>
  """
    tester = self.assertNotContains if reversed else self.assertContains
    response = response or self.client.get(reverse("members:birthdays"))
    tester(response, no_bdays, html=True)


class TestBirthdays(TestBirthdaysMixin, MemberTestCase):
  def test_birthday_today(self):
    """Tests that the birthday today view works correctly."""
    # create a member with birthday = today
    today = date.today()
    b_today = date(2000, today.month, today.day)
    member = self.get_member_with_bday(b_today)
    self.check_birthday_today(member)

  def test_birthdays_tomorrow(self):
    """Tests that the birthdays tomorrow view works correctly."""
    today = date.today()
    # create a member with birthdate = tomorrow - 2 years
    b_tomorrow = date(1998, today.month, today.day) + timedelta(days=1)
    member = self.get_member_with_bday(b_tomorrow)
    self.check_birthdays_tomorrow(member)

  def test_birthdays_after_tomorrow(self):
    """Tests that the birthdays after tomorrow view works correctly."""
    today = date.today()
    # create a member with birthdate in 2 weeks
    b_2weeks = date(1990, today.month, today.day) + timedelta(weeks=2)
    member = self.get_member_with_bday(b_2weeks)
    self.check_birthdays_after_tomorrow(member)
