from django.conf import settings
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from .tests_member import MemberTestCase
from datetime import date, timedelta


class TestBirthdaysMixin():
  def get_member_with_bday(self, bday):
    # create a member with birthday = bday
    new_data = self.get_new_member_data()
    new_data['birthdate'] = bday
    return self.create_member(new_data)

  def check_birthday(self, member, expected_chain, response=None, reversed=False):
    response = response or self.client.get(reverse("members:birthdays"))
    common_chain = '''
      <div class="cell has-background-light-link has-text-right px-0 mx-0">
        <a href="/members/%(member_id)s/">%(first_name)s %(last_name)s</a>
      </div>
    '''
    tester = self.assertNotContains if reversed else self.assertContains
    tester(response, common_chain % {"member_id": member.id,
                                     "first_name": member.first_name,
                                     "last_name": member.last_name}, html=True)

    tester(response, expected_chain, html=True)

  def check_birthday_today(self, member, response=None, reversed=False):
    b_is_today = _("turns %(age)s today, happy birthday!") % {'age': member.age()}
    c_is_today = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-danger">
        {b_is_today}
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
      </div>
    '''
    self.check_birthday(member, c_is_today, response, reversed)

  def check_birthdays_tomorrow(self, member, response=None, reversed=False):
    b_is_tomorrow = _("will turn %(age)s tomorrow, happy birthday!") % {'age': member.age()+1}
    c_is_tomorrow = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-warning">
        {b_is_tomorrow}
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
      </div>
    '''
    self.check_birthday(member, c_is_tomorrow, response, reversed)

  def check_birthdays_after_tomorrow(self, member, response=None, reversed=False):
    b_date = date_format(member.next_birthday(), "l d F", use_l10n=True)
    b_is_after = _("will turn %(age)s on %(birthday)s") % {'age': member.age()+1, 'birthday': b_date}
    c_is_after = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-primary">
        {b_is_after}
      </div>
    '''
    self.check_birthday(member, c_is_after, response, reversed)

  def check_no_birthdays(self, response=None, reversed=False):
    no_bdays = f'''
  <div>
    <p>{_("No birthdays in next %(ndays)s days") % {'ndays': settings.BIRTHDAY_DAYS}}.</p>
  </div>
  '''
    tester = self.assertNotContains if reversed else self.assertContains
    response = response or self.client.get(reverse("members:birthdays"))
    tester(response, no_bdays, html=True)


class TestBirthdays(TestBirthdaysMixin, MemberTestCase):
  def test_birthday_today(self):
    # create a member with birthday = today
    today = date.today()
    b_today = date(2000, today.month, today.day)
    member = self.get_member_with_bday(b_today)
    self.check_birthday_today(member)

  def test_birthdays_tomorrow(self):
    today = date.today()
    # create a member with birthdate = tomorrow - 2 years
    b_tomorrow = date(1998, today.month, today.day) + timedelta(days=1)
    member = self.get_member_with_bday(b_tomorrow)
    self.check_birthdays_tomorrow(member)

  def test_birthdays_after_tomorrow(self):
    today = date.today()
    # create a member with birthdate in 2 weeks
    b_2weeks = date(1990, today.month, today.day) + timedelta(weeks=2)
    member = self.get_member_with_bday(b_2weeks)
    self.check_birthdays_after_tomorrow(member)
