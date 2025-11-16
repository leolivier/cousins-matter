from urllib.parse import urlencode

from django.conf import settings
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _, ngettext
from django.core.exceptions import ValidationError
from django.test import tag

from chat.tests.tests_mixin import ChatMessageSenderMixin
from members.tests.tests_member_base import MemberTestCase
from cm_main.tests.test_django_q import django_q_sync_class
from ..models import ChatMessage, ChatRoom


class ChatRoomTests(MemberTestCase):
  def do_check_chat_room(self, room_name, slug):
    url = reverse('chat:new_room') + '?' + urlencode({'name': room_name})
    response = self.client.get(url, follow=True)
    # self.print_response(response)
    # should be redirected to room detail. if not, it means there was an error
    self.assertTemplateUsed(response, 'chat/room_detail.html')
    self.assertContains(response, f'<span id="show-room-name">{room_name}</span>', html=True)
    follow = _('Follow')
    self.assertContains(response, f'''
<a class="button " href="{reverse("chat:toggle_follow", args=[slug])}"
   aria-label="{follow}" title="{follow}">
  <span class="icon is-large">
    <i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i>
  </span>
  <span>{follow}</span>
</a>''', html=True)
    rooms = ChatRoom.objects.filter(slug=slug)
    self.assertEqual(rooms.count(), 1)
    return rooms.first()

  def test_create_chat_room(self):
    """Tests creating a public chat room."""
    room_name = 'a clean room'
    slug = slugify(room_name)
    self.assertFalse(ChatRoom.objects.filter(slug=slug).exists())
    self.do_check_chat_room(room_name, slug)
    # try a second time with the exact same name
    # the way it is coded, this will redirect to the existing room and create an error
    self.do_check_chat_room(room_name, slug)
    # now, try with a direct creation, and check it raises a ValidationError
    with self.assertRaises(ValidationError):
      ChatRoom.objects.create(name=room_name)
    # and finally, try with a different room name but which has the same slug
    new_room_name = '#' + room_name + '!'
    new_slug = slugify(new_room_name)
    self.assertEqual(new_slug, slug)
    url = reverse('chat:new_room') + '?' + urlencode({'name': new_room_name})
    response = self.client.get(url, follow=True)
    # self.print_response(response)
    self.assertContainsMessage(response, 'error',
                               _("Another room with a similar name already exists ('%(similar_room_name)s'). "
                                 "Please choose a different name.") % {'similar_room_name': room_name})
    ChatRoom.objects.all().delete()

  def test_list_rooms(self):
    """Tests listing public chat rooms."""
    rooms = [ChatRoom.objects.create(name='Chat Room #%i' % i) for i in range(5)]
    ChatMessage.objects.create(room=rooms[0], content='a message', member=self.member)
    response = self.client.get(reverse('chat:chat_rooms'))
    # self.print_response(response)
    nmsgs = ngettext('%(nmsgs)s message', '%(nmsgs)s messages', 1) % {'nmsgs': 1}
    nfollowers = ngettext('%(nfollowers)s follower', '%(nfollowers)s followers', 0) % {'nfollowers': 0}
    follow = _('Follow')
    profile = _('profile')
    self.assertContains(response, f'''
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
    <img class="is-rounded" src="{self.member.avatar_mini_url}" alt="{self.member.username}">
  </div>
  <div class="is-flex-shrink-1 has-text-primary has-text-weight-bold mr-5">
    {self.member.full_name}
    <a href="{reverse("members:detail", kwargs={'pk': self.member.id})}" aria-label="{profile}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-open-in-new" aria-hidden="true"></i></span>
    </a>
    <br>
    <span class="tag mr-3">{nmsgs}</span>
    <span class="tag ">{nfollowers}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse('chat:room', args=[rooms[0].slug])}">{rooms[0].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[0].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i></span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>
''', html=True)
    nmsgs = ngettext('%(nmsgs)s message', '%(nmsgs)s messages', 0) % {'nmsgs': 0}
    nobody = _('No author yet')
    for i in range(1, 5):
      self.assertContains(response, f'''
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
      <img class="is-rounded" src="{settings.DEFAULT_AVATAR_URL}" alt="{nobody}">
  </div>
  <div class="is-flex-shrink-1 has-text-primary has-text-weight-bold mr-5">
    {nobody}
    <span class="icon has-text-link is-large"><i class="mdi mdi-24px mdi-chat" aria-hidden="true"></i></span>
    <br>
    <span class="tag mr-3">{nmsgs}</span>
    <span class="tag ">{nfollowers}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse('chat:room', args=[rooms[i].slug])}">{rooms[i].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[i].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i></span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>''', html=True)
    ChatRoom.objects.all().delete()


@tag("needs-redis")
@django_q_sync_class
class ChatMessageTests(ChatMessageSenderMixin, MemberTestCase):
  async def test_chat_consumer(self):
    """Tests the chat consumer."""
    msg = 'this is my message to the world!'
    communicator = await self.send_chat_message(msg, self.slug, disconnect=False)
    response = await communicator.receive_json_from()
    # print(response)
    self.assertTrue('args' in response)
    self.assertEqual(response['args']['message'], msg)
    self.assertEqual(response['args']['username'], self.member.username)
    message = await ChatMessage.objects.filter(room=self.room).afirst()
    self.assertIsNotNone(message)
    self.assertEqual(response['args']['message'], message.content)
    self.assertEqual(self.member.id, message.member_id)
    # Close communication
    await communicator.disconnect()

    # now, update the message and check it is updated
    new_msg = 'this is my updated message to the world!'
    communicator = await self.send_updated_message(self.slug, message.id, new_msg, disconnect=False)
    response = await communicator.receive_json_from()

    self.assertTrue('args' in response)
    self.assertEqual(response['args']['message'], new_msg)
    self.assertEqual(response['args']['msgid'], message.id)
    await message.arefresh_from_db()
    self.assertEqual(message.content, new_msg)
    # Close communication
    await communicator.disconnect()

    # now, delete the message and check it is deleted
    await self.send_delete_message(self.slug, message.id)
    await message.arefresh_from_db()
    self.assertEqual(message.content, '**This message has been deleted**')
