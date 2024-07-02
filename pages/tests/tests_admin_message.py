from django.conf import settings
from django.urls import reverse
from members.tests.tests_member_base import MemberTestCase
from ..models import create_page
from .test_base import BasePageTestCase, TestPageMixin


class TestAdminMessage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def setUp(self):
    super().setUp()
    create_page(
      url=f'/pages/{settings.LANGUAGE_CODE}/home/authenticated/',
      title='a home page',
      content="a home page content we don't care")

  def test_admin_message(self):
    admin_message = {
      'url': "/pages/admin-message/",
      'title': "unused",
      'content': "a wonderful message from the administrator"
    }
    adm_msg = create_page(**admin_message)
    self.assertIsNotNone(adm_msg)
    response = self.client.get(reverse('cm_main:Home'), follow=True)
    # self.print_response(response)
    self.assertContains(response, f'''<div class="notification is-info">
        <button class="delete"></button>
        {admin_message['content']}
      </div>''', html=True)

  def test_admin_messages(self):
    admin_messages = [
      {
        'url': "/pages/admin-message/1rst/",
        'title': "unused1",
        'content': "a 1rst wonderful message from the administrator"
      },
      {
        'url': "/pages/admin-message/2nd/",
        'title': "unused2",
        'content': "a 2nd wonderful message from the administrator"
      },
    ]
    for admin_message in admin_messages:
      create_page(**admin_message)
    response = self.client.get(reverse('cm_main:Home'), follow=True)
    for admin_message in admin_messages:
      self.assertContains(response, f'''<div class="notification is-info">
          <button class="delete"></button>
          {admin_message['content']}
        </div>''', html=True)
