from django.urls import reverse
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from .tests_member import MemberTestCase
from datetime import date, timedelta


class TestBirthdays(MemberTestCase):
  def test_birthdays(self):
    today = date.today()
    b_today = date(2000, today.month, today.day)
    # create a member with birthday = today
    new_data = self.get_new_member_data()
    new_data['birthdate'] = b_today
    member1 = self.create_member(new_data)
    # create a member with birthdate = tomorrow - 2 years
    new_data = self.get_new_member_data()
    b_tomorrow = date(1998, today.month, today.day) + timedelta(days=1)
    new_data['birthdate'] = b_tomorrow
    member2 = self.create_member(new_data)
    # create a member with birthdate in 2 weeks
    new_data = self.get_new_member_data()
    b_2weeks = date(1990, today.month, today.day) + timedelta(weeks=2)
    new_data['birthdate'] = b_2weeks
    member3 = self.create_member(new_data)

    response = self.client.get(reverse("members:birthdays"))
    # pprint(vars(response))

    common_chain = '''
      <div class="cell has-background-light-link has-text-right px-0 mx-0">
        <a href="/members/%(member_id)s/">%(first_name)s %(last_name)s</a>
      </div>
    '''
    self.assertContains(response, common_chain % {"member_id": member1.id,
                                                  "first_name": member1.first_name,
                                                  "last_name": member1.last_name}, html=True)
    self.assertContains(response, common_chain % {"member_id": member2.id,
                                                  "first_name": member2.first_name,
                                                  "last_name": member2.last_name}, html=True)
    self.assertContains(response, common_chain % {"member_id": member3.id,
                                                  "first_name": member3.first_name,
                                                  "last_name": member3.last_name}, html=True)

    b_is_today = _("turns %(age)s today, happy birthday!") % {'age': member1.age()}
    c_is_today = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-danger">
        {b_is_today}
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
      </div>
    '''
    self.assertContains(response, c_is_today, html=True)

    b_is_tomorrow = _("will turn %(age)s tomorrow, happy birthday!") % {'age': member2.age()+1}
    c_is_tomorrow = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-warning">
        {b_is_tomorrow}
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant"></span></i>
        <i class="icon"><span class="mdi mdi-cake-variant-outline"></span></i>
      </div>
    '''
    self.assertContains(response, c_is_tomorrow, html=True)

    b_date = date_format(member3.next_birthday(), "l d F", use_l10n=True)
    b_is_after = _("will turn %(age)s on %(birthday)s") % {'age': member3.age()+1, 'birthday': b_date}
    c_is_after = f'''
      <div class="cell has-background-light-primary px-0 mx-0 has-text-primary">
        {b_is_after}
      </div>
    '''
    self.assertContains(response, c_is_after, html=True)
