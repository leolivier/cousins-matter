import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from members.models import Member
from ..models import PrivateChatRoom, ChatRoom, ChatMessage
from cm_main import followers
from cm_main.utils import PageOutOfBounds, Paginator
from urllib.parse import unquote

logger = logging.getLogger(__name__)


@login_required
def list_chat_rooms(request, page_num=1, private=False):
    """
    Renders a page displaying a list of chat rooms (public or private and only the ones the user is
    a member of if private), along with information about the author of the first message in each
    room. This view is accessible only to authenticated users.

    Parameters:
      - `request` (HttpRequest): The HTTP request object.
      - 'private' (bool, optional): Whether the chat rooms to display are private. Defaults to False.
      - `page_num` (int, optional): The page number of the chat rooms to display. Defaults to 1.

    Returns:
      - `HttpResponse`: The HTTP response object containing the rendered template with the private
        chat rooms and their authors.

    Raises:
      - `None`

    """
    # Subquery to get the author of the first related ChatMessage instance of a private room
    first_msg_auth_subquery = (
        ChatMessage.objects.filter(room=OuterRef("pk"))
        .order_by("date_added")[:1]
        .select_related("member")
        .values("member_id")
    )
    if private:
        # look for private rooms of which the user who sent the request is member
        chat_rooms = PrivateChatRoom.objects.filter(followers=request.user)
    else:
        chat_rooms = ChatRoom.objects.public()
    # Annotate room instances with the first message and the number of messages in the room
    chat_rooms = chat_rooms.annotate(
        num_messages=Count("chatmessage"),
        first_message_author=Subquery(first_msg_auth_subquery),
    ).order_by("date_added")

    try:
        page = Paginator.get_page(
            request,
            chat_rooms,
            page_num,
            reverse_link="chat:private_chat_page" if private else "chat:chat_page",
            default_page_size=settings.DEFAULT_CHATROOMS_PER_PAGE,
        )
        author_ids = [
            room.first_message_author
            for room in page.object_list
            if room.first_message_author is not None
        ]
        # print("author ids", author_ids)
        authors = Member.objects.filter(id__in=author_ids)
        for room in page.object_list:
            if room.first_message_author:
                # print("first msg auth=", room.first_message_author)
                for author in authors:
                    # print("author name:", author.username)
                    if room.first_message_author == author.id:
                        room.first_message_author = author
                # print("final author:", room.first_message_author)
        return render(
            request, "chat/chat_rooms.html", {"page": page, "private": private}
        )
    except PageOutOfBounds as exc:
        return redirect(exc.redirect_to)


@login_required
def create_chat_room(request, private=False):
    """
    Creates a new public or private chat room with the given name for the authenticated user.

    Args:
        request (HttpRequest): The HTTP request object containing the 'name' parameter
                               in the GET request.
        private (bool, optional): Whether the chat room is private. Defaults to False.

    Returns:
        HttpResponse: The HTTP response object redirecting to the newly created private
                      chat room.

    Raises:
        ValidationError: If the room name is invalid.

    """
    room_name = unquote(request.GET["name"])
    room_class = PrivateChatRoom if private else ChatRoom
    try:
        new_room, created = room_class.objects.get_or_create(name=room_name)
        urlpath = "chat:private_room" if private else "chat:room"
        room_url = reverse(urlpath, args=[new_room.slug])
        if created:
            if private:
                # if room was created, add user who created it as member (ie followers which is reused for that) and admins
                logger.debug(
                    "private room created, adding user who created it as member and admin"
                )
                new_room.followers.add(request.user)
                new_room.admins.add(request.user)
                new_room.save()
                # even if room was created, we don't check user followers because:
                # IT MIGHT NOT BE ADAPTED; IF SOMEONE CREATES A PRIVATE ROOM AND DOES NOT WANT TO INVITE HIS/HER FOLLOWERS,
                # NO NEED TO TELL THE FOLLOWERS THAT HE/SHE CREATED THE ROOM WHERE THE FOLLOWER WON'T BE ADDED
                # followers.check_followers(request, private_room, request.user, room_url)
            else:
                # if room was created, check user followers
                logger.debug("public room created, checking followers")
                followers.check_followers(request, new_room, request.user, room_url)
        else:
            if not private and not new_room.is_public():
                raise ValidationError(
                    _("A private room with almost the same name already exists: %s")
                    % new_room.name
                )
            elif private and new_room.is_public():
                raise ValidationError(
                    _("A public room with almost the same name already exists: %s")
                    % new_room.name
                )
        return redirect(room_url)
    except ValidationError as ve:
        for error in ve:
            match error[0]:
                case "__all__":
                    messages.error(request, " ".join(error[1]))
                case "slug":
                    similar_room = room_class.objects.get(slug=slugify(room_name))
                    messages.error(
                        request,
                        _(
                            "Another room with a similar name already exists ('%(similar_room_name)s'). "
                            "Please choose a different name."
                        )
                        % {"similar_room_name": similar_room.name},
                    )
                case _:
                    messages.error(request, f'{error[0]}: {" ".join(error[1])}')
        return redirect(reverse("chat:private_chat_rooms"))


@login_required
def display_chat_room(request, room_slug, private=False, page_num=None):
    """
    View function for displaying a chat room. When private is True, it displays a private chat room.

    The user must be authenticated to access this view.

    Parameters:
        request (HttpRequest): The HTTP request object.
        room_slug (str): The slug of the private chat room.
        private (bool, optional): Whether the chat room is private. Defaults to False.
        page_num (int, optional): The page number of the chat messages to display. Defaults to None.

    Returns:
        HttpResponse: The HTTP response object containing the rendered template for the private chat room.

    Raises:
        Http404: If the private chat room with the given slug does not exist.

    This function retrieves the chat room with the given slug using `get_object_or_404` from the `ChatRoom` model if private
    is False, or the `PrivateChatRoom` model if True.
    When private, it checks if the authenticated user is a member of the private chat room by checking if the user is present
    in the `followers` field of the room.
    If the user is not a member, an error message is displayed and the user is redirected to the private chat rooms page.

    The function then retrieves the chat messages for the chat room and calculates the page size for displaying the
    messages. The page size is either retrieved from the `page_size` parameter in the request GET parameters or from the
    `DEFAULT_CHATMESSAGES_PER_PAGE` setting.

    The function creates a paginator object `ptor` using the `Paginator` class from Django, passing the chat messages and the
    page size as arguments. It also defines a lambda function `compute_link` to generate the link for each page.

    If the `page_num` parameter is not provided, the function sets it to the total number of pages in the paginator.
    If the `page_num` is out of range, the function redirects the user to the last page.

    Finally, the function retrieves the page data for the specified page number using the `get_page_data` method of the
    paginator object and renders the template `chat/room_detail.html` with the room and page data as context.

    Note: The `reverse` function is used to generate URLs for redirecting the user. The `urlencode` function is used to encode
    the query parameters for the URL.
    """
    room = get_object_or_404(
        ChatRoom if not private else PrivateChatRoom, slug=room_slug
    )
    if private and request.user not in room.followers.all():
        messages.error(request, _("You are not a member of this private room"))
        return redirect(reverse("chat:private_chat_rooms"))
    message_list = ChatMessage.objects.filter(room=room.id).order_by("date_added", "id")
    try:
        page = Paginator.get_page(
            request,
            message_list,
            page_num=page_num,
            reverse_link="chat:room_page",
            compute_link=lambda page_num: reverse(
                "chat:room_page", args=[room_slug, page_num]
            ),
            default_page_size=settings.DEFAULT_CHATMESSAGES_PER_PAGE,
        )
        last_msg = message_list.last()
        last_date = last_msg.date_added.strftime("%Y-%m-%d") if message_list else None
        last_sender = last_msg.member.username if message_list else None
        # print("last date found", last_date)
        return render(
            request,
            "chat/room_detail.html",
            {
                "room": room,
                "page": page,
                "private": private,
                "last_date": last_date,
                "last_sender": last_sender,
            },
        )
    except PageOutOfBounds as exc:
        return redirect(exc.redirect_to)
