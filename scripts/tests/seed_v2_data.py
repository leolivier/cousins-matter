"""Seed a v2 database with one legacy row per tenant-scoped app.

Runs inside the v2 image (see scripts/tests/test_upgrade_v2_v3.sh), so it must
only use fields that exist in v2. The post-upgrade checker then verifies that
every row survived and was assigned to the default tenant.
"""

import base64
from datetime import date

from django.core.files.base import ContentFile

from chat.models import ChatMessage, ChatRoom
from classified_ads.models import ClassifiedAd
from forum.models import Message, Post
from galleries.models import Gallery
from genealogy.models import Person
from members.models import Member
from polls.models import Poll
from troves.models import Trove

member, _ = Member.objects.get_or_create(
  username="legacy-member",
  defaults={
    "email": "legacy-member@example.com",
    "first_name": "Legacy",
    "last_name": "Member",
    "birthdate": date(1990, 1, 1),
  },
)
member.set_password("legacy-password")
member.save()

gallery = Gallery(name="Legacy gallery", slug="legacy-gallery", owner=member)
gallery.save()

message = Message.objects.create(author=member, content="Legacy forum message")
Post.objects.create(title="Legacy post", first_message=message)

Poll.objects.create(title="Legacy poll", owner=member)

ClassifiedAd.objects.create(
  title="Legacy ad",
  category="other",
  subcategory="other",
  description="Legacy classified ad",
  price="0",
  owner=member,
)

# Trove.save() validates the picture and builds a thumbnail, so pass a real
# (1x1) PNG rather than an empty file.
PNG_1PX = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
Trove.objects.create(
  title="Legacy trove",
  description="Legacy trove",
  picture=ContentFile(PNG_1PX, name="legacy.png"),
  category="history",
  owner=member,
)

Person.objects.create(first_name="Legacy", last_name="Person", sex="O")

room = ChatRoom.objects.create(name="Legacy room", slug="legacy-room")
ChatMessage.objects.create(member=member, room=room, content="Legacy chat message")

print("seeded v2 data")
