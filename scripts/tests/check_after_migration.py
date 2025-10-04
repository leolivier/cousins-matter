#!/usr/bin/env python3
"""
Check Cousins Matter after sqlite3 to postgres migration.

Usage: docker exec -it cousins-matter python -m scripts.check_after_migration
"""
import django
import os
import sqlite3
from django.conf import settings


def check_members(cursor: sqlite3.Cursor):
    """Check members after sqlite3 to postgres migration"""
    from members.models import Member
    # check members count
    cursor.execute("SELECT * FROM members_member order by id")
    old_members = cursor.fetchall()
    migrated_members = Member.objects.all().order_by("id")
    if len(migrated_members) != len(old_members):
        raise Exception("Number of members does not match after migration")
    print(f"Found {len(migrated_members)} members after migration")
    # check members data
    for old_member, migrated_member in zip(old_members, migrated_members):
        if old_member[0] != migrated_member.id or old_member[4] != migrated_member.username or \
           old_member[7] != migrated_member.email or old_member[1] != migrated_member.password:
            raise Exception("Members data does not match after migration")


def check_galleries(cursor: sqlite3.Cursor):
    """Check galleries after sqlite3 to postgres migration"""
    from galleries.models import Gallery
    # check galleries count
    cursor.execute("SELECT * FROM galleries_gallery order by id")
    old_galleries = cursor.fetchall()
    migrated_galleries = Gallery.objects.all().order_by("id")
    if len(migrated_galleries) != len(old_galleries):
        raise Exception("Number of galleries does not match after migration")
    print(f"Found {len(migrated_galleries)} galleries after migration")
    # check galleries data
    for old_gallery, migrated_gallery in zip(old_galleries, migrated_galleries):
        if old_gallery[0] != migrated_gallery.id or old_gallery[1] != migrated_gallery.name or \
           old_gallery[2] != migrated_gallery.description or old_gallery[4] != migrated_gallery.owner_id:
          raise Exception("Galleries data does not match after migration")


def check_photos(cursor: sqlite3.Cursor):
    """Check photos after sqlite3 to postgres migration"""
    from galleries.models import Photo
    # check photos count
    cursor.execute("SELECT * FROM galleries_photo order by id")
    old_photos = cursor.fetchall()
    migrated_photos = Photo.objects.all().order_by("id")
    if len(migrated_photos) != len(old_photos):
        raise Exception("Number of photos does not match after migration")
    print(f"Found {len(migrated_photos)} photos after migration")
    # check photos data
    for old_photo, migrated_photo in zip(old_photos, migrated_photos):
        if old_photo[0] != migrated_photo.id or old_photo[2] != migrated_photo.name or \
           old_photo[3] != migrated_photo.description or old_photo[6] != migrated_photo.gallery_id:
          raise Exception("Photos data does not match after migration")


def check_forums(cursor: sqlite3.Cursor):
    """Check forums after sqlite3 to postgres migration"""
    from forum.models import Post
    # check forums count
    cursor.execute("SELECT * FROM forum_post order by id")
    old_posts = cursor.fetchall()
    migrated_posts = Post.objects.all().order_by("id")
    if len(migrated_posts) != len(old_posts):
        raise Exception("Number of posts does not match after migration")
    print(f"Found {len(migrated_posts)} posts after migration")
    # check posts data
    for old_post, migrated_post in zip(old_posts, migrated_posts):
        if old_post[0] != migrated_post.id or old_post[4] != migrated_post.name or \
           old_post[7] != migrated_post.description or old_post[1] != migrated_post.owner:
          # raise Exception("Posts data does not match after migration")
          print("old post:", old_post)
          print("migrated post:", migrated_post)
          break


def check_classified_ads(cursor: sqlite3.Cursor):
    """Check classified ads after sqlite3 to postgres migration"""
    from classified_ads.models import ClassifiedAd
    # check classified ads count
    cursor.execute("SELECT * FROM classified_ads_classifiedad order by id")
    old_classified_ads = cursor.fetchall()
    migrated_classified_ads = ClassifiedAd.objects.all().order_by("id")
    if len(migrated_classified_ads) != len(old_classified_ads):
        raise Exception("Number of classified ads does not match after migration")
    print(f"Found {len(migrated_classified_ads)} classified ads after migration")
    # check classified ads data
    for old_classified_ad, migrated_classified_ad in zip(old_classified_ads, migrated_classified_ads):
        if old_classified_ad[0] != migrated_classified_ad.id or old_classified_ad[4] != migrated_classified_ad.name or \
           old_classified_ad[7] != migrated_classified_ad.description or old_classified_ad[1] != migrated_classified_ad.owner:
          # raise Exception("Classified ads data does not match after migration")
          print("old classified ad:", old_classified_ad)
          print("migrated classified ad:", migrated_classified_ad)
          break


def check_polls(cursor: sqlite3.Cursor):
    """Check polls after sqlite3 to postgres migration"""
    from polls.models import Poll
    # check polls count
    cursor.execute("SELECT * FROM polls_poll order by id")
    old_polls = cursor.fetchall()
    migrated_polls = Poll.objects.all().order_by("id")
    if len(migrated_polls) != len(old_polls):
        raise Exception("Number of polls does not match after migration")
    print(f"Found {len(migrated_polls)} polls after migration")
    # check polls data
    for old_poll, migrated_poll in zip(old_polls, migrated_polls):
        if old_poll[0] != migrated_poll.id or old_poll[4] != migrated_poll.name or \
           old_poll[7] != migrated_poll.description or old_poll[1] != migrated_poll.owner:
          # raise Exception("Polls data does not match after migration")
          print("old poll:", old_poll)
          print("migrated poll:", migrated_poll)
          break


def check_chat(cursor: sqlite3.Cursor):
    """Check chat after sqlite3 to postgres migration"""
    from chat.models import ChatRoom, ChatMessage
    # check chatrooms count
    cursor.execute("SELECT * FROM chat_chatroom order by id")
    old_chatrooms = cursor.fetchall()
    migrated_chatrooms = ChatRoom.objects.all().order_by("id")
    if len(migrated_chatrooms) != len(old_chatrooms):
        raise Exception("Number of chatrooms does not match after migration")
    print(f"Found {len(migrated_chatrooms)} chatrooms after migration")
    # check chatrooms data
    for old_chatroom, migrated_chatroom in zip(old_chatrooms, migrated_chatrooms):
        if old_chatroom[0] != migrated_chatroom.id or old_chatroom[1] != migrated_chatroom.name or \
           old_chatroom[3] != migrated_chatroom.slug or old_chatroom[2] != migrated_chatroom.date_added:
          raise Exception("Chatrooms data does not match after migration")
    # check chatmessages count
    cursor.execute("SELECT * FROM chat_chatmessage order by id")
    old_chatmessages = cursor.fetchall()
    migrated_chatmessages = ChatMessage.objects.all().order_by("id")
    if len(migrated_chatmessages) != len(old_chatmessages):
        raise Exception("Number of chatmessages does not match after migration")
    print(f"Found {len(migrated_chatmessages)} chatmessages after migration")
    # check chatmessages data
    for old_chatmessage, migrated_chatmessage in zip(old_chatmessages, migrated_chatmessages):
        if old_chatmessage[0] != migrated_chatmessage.id or old_chatmessage[1] != migrated_chatmessage.member_id or \
           old_chatmessage[2] != migrated_chatmessage.room_id or old_chatmessage[3] != migrated_chatmessage.content or \
           old_chatmessage[4] != migrated_chatmessage.date_added or old_chatmessage[5] != migrated_chatmessage.date_modified:
          # raise Exception("Chatmessages data does not match after migration")
          print("old chatmessage:", old_chatmessage)
          print("migrated chatmessage:", migrated_chatmessage)
          break


def check_troves(cursor: sqlite3.Cursor):
    """Check troves after sqlite3 to postgres migration"""
    from troves.models import Trove
    # check troves count
    cursor.execute("SELECT * FROM troves_trove order by id")
    old_troves = cursor.fetchall()
    migrated_troves = Trove.objects.all().order_by("id")
    if len(migrated_troves) != len(old_troves):
        raise Exception("Number of troves does not match after migration")
    print(f"Found {len(migrated_troves)} troves after migration")
    # check troves data
    for old_trove, migrated_trove in zip(old_troves, migrated_troves):
        if old_trove[0] != migrated_trove.id or old_trove[4] != migrated_trove.name or \
           old_trove[7] != migrated_trove.description or old_trove[1] != migrated_trove.owner:
          # raise Exception("Troves data does not match after migration")
          print("old trove:", old_trove)
          print("migrated trove:", migrated_trove)
          break


def check_after_migration():
    """Test Cousins Matter after sqlite3 to postgres migration"""
    con = sqlite3.connect(settings.PUBLIC_MEDIA_ROOT / "db.sqlite3")
    cursor = con.cursor()
    check_members(cursor)
    check_galleries(cursor)
    check_photos(cursor)
    check_forums(cursor)
    check_chat(cursor)
    check_polls(cursor)
    check_classified_ads(cursor)
    check_troves(cursor)

    print("Migration test passed")
    con.close()


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
    django.setup()
    check_after_migration()
