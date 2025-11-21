from django.conf import settings
from django.urls import path

from .views import views_private_rooms, views_public_rooms, views_test

app_name = "chat"
urlpatterns = [
    # public rooms
    path("", views_public_rooms.chat_rooms, name="chat_rooms"),
    path("<int:page_num>", views_public_rooms.chat_rooms, name="chat_page"),
    path("room", views_public_rooms.new_room, name="new_room"),
    path(
        "room/<str:room_slug>", views_public_rooms.display_public_chat_room, name="room"
    ),
    path(
        "room/<str:room_slug>/<int:page_num>",
        views_public_rooms.display_public_chat_room,
        name="room_page",
    ),
    path(
        "room/<str:room_slug>/toggle-follow",
        views_public_rooms.toggle_follow,
        name="toggle_follow",
    ),
    path("room/<str:room_slug>/edit", views_public_rooms.edit_room, name="room-edit"),
    path(
        "room/<str:room_slug>/delete",
        views_public_rooms.delete_room,
        name="room-delete",
    ),
    # private rooms
    path("private", views_private_rooms.private_chat_rooms, name="private_chat_rooms"),
    path(
        "private/<int:page_num>",
        views_private_rooms.private_chat_rooms,
        name="private_chat_page",
    ),
    path("private/room", views_private_rooms.new_private_room, name="new_private_room"),
    path(
        "private/room/<str:room_slug>",
        views_private_rooms.display_private_chat_room,
        name="private_room",
    ),
    path(
        "private/room/<str:room_slug>/<int:page_num>",
        views_private_rooms.display_private_chat_room,
        name="private_room_page",
    ),
    path(
        "private/room/<str:room_slug>/add_member/",
        views_private_rooms.add_member_to_private_room,
        name="add_member_to_private_room",
    ),
    path(
        "private/room/<str:room_slug>/add_admin/",
        views_private_rooms.add_admin_to_private_room,
        name="add_admin_to_private_room",
    ),
    path(
        "private/room/<str:room_slug>/remove_member/<int:member_id>",
        views_private_rooms.remove_member_from_private_room,
        name="remove_member_from_private_room",
    ),
    path(
        "private/room/<str:room_slug>/remove_admin/<int:member_id>",
        views_private_rooms.remove_admin_from_private_room,
        name="remove_admin_from_private_room",
    ),
    path(
        "private/room/<str:room_slug>/leave/",
        views_private_rooms.leave_private_room,
        name="leave_private_room",
    ),
    path(
        "private/room/<str:room_slug>/admin_leave/",
        views_private_rooms.leave_private_room_admins,
        name="leave_private_room_admins",
    ),
    path(
        "private/room/<str:room_slug>/members/",
        views_private_rooms.list_private_room_members,
        name="private_room_members",
    ),
    path(
        "private/room/<str:room_slug>/admins/",
        views_private_rooms.list_private_room_admins,
        name="private_room_admins",
    ),
    path(
        "private/room/<str:room_slug>/search_members",
        views_private_rooms.search_private_members,
        name="search_private_members",
    ),
]
if settings.DEBUG:
    urlpatterns += [
        path(
            "test/create_rooms/<int:num_rooms>",
            views_test.create_test_rooms,
            name="test_create_rooms",
        ),
        path(
            "test/create_messages/<int:num_messages>",
            views_test.create_test_messages,
            name="test_create_messages",
        ),
    ]
