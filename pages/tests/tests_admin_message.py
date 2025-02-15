from django.conf import settings
from django.urls import reverse
from members.tests.tests_member_base import MemberTestCase
from ..models import create_page
from .test_base import BasePageTestCase
from .tests_homepage import TestHomePageMixin


class TestAdminMessage(TestHomePageMixin, BasePageTestCase, MemberTestCase):

  def test_admin_message(self):
    admin_message = {
      'url': settings.ADMIN_MESSAGE_PAGE_URL_PREFIX + "/",
      'title': "unused",
      'content': "a wonderful message from the administrator"
    }
    adm_msg = create_page(**admin_message)
    self.assertIsNotNone(adm_msg)
    response = self.client.get(reverse('cm_main:Home'), follow=True)
    # self.print_response(response)
    self.assertContains(response, f'''<div class="notification is-info admin-message" data-id="{adm_msg.id}">
        <button class="delete"></button>
        {admin_message['content']}
      </div>''', html=True)

  def test_admin_messages(self):
    admin_messages = [
      {
        'url': settings.ADMIN_MESSAGE_PAGE_URL_PREFIX + "/1rst/",
        'title': "unused1",
        'content': "a 1rst wonderful message from the administrator"
      },
      {
        'url': settings.ADMIN_MESSAGE_PAGE_URL_PREFIX + "/2nd/",
        'title': "unused2",
        'content': "a 2nd wonderful message from the administrator"
      },
    ]
    for admin_message in admin_messages:
      admin_message['obj'] = create_page(**admin_message)
    response = self.client.get(reverse('cm_main:Home'), follow=True)
    for admin_message in admin_messages:
      self.assertContains(response, f'''<div class="notification is-info admin-message" data-id="{admin_message['obj'].id}">
          <button class="delete"></button>
          {admin_message['content']}
        </div>''', html=True)
