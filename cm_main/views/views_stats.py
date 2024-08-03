import logging
from urllib.error import HTTPError
from urllib.request import urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

import json
from packaging import version

from chat.models import ChatMessage, ChatRoom, PrivateChatRoom
from forum.models import Comment, Message, Post
from galleries.models import Gallery, Photo
from members.models import Member

logger = logging.getLogger(__name__)


def get_github_release_version(request, owner, repo):
    """
    Retrieves the latest release version of a GitHub repository.

    :param request: Django request object
    :param owner: Repository owner
    :param repo: Repository name
    :return: JSON response with version of latest release or error message if not found
    """

    url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
    try:
      with urlopen(url) as response:
        data = response.read()
        json_data = json.loads(data)
        if 'tag_name' in json_data:
          return json_data['tag_name']
        else:
          messages.error(request, _("Version not found"))
          return None
    except HTTPError as e:
      messages.error(request, e.msg)
      return None


def get_latest_release_text(request):
  latest_release = get_github_release_version(request, 'leolivier', 'cousins-matter')
  # print('latest_release', latest_release)
  if latest_release is not None:
    latest_version = version.parse(latest_release)
    current_version = version.parse(settings.APP_VERSION)
    if current_version < latest_version:
      release_warning = _("Your version is not up-to-date.")
      if request.user.is_superuser:
        release_warning += "<br>"
        release_warning += _("Please update it by running the following command:<br><code>docker-start.sh -u</code>")
        release_warning = mark_safe(release_warning)

      latest_release = {
        'value': latest_release,
        'warning': release_warning,
        'icon': 'poop'
      }
    elif current_version == latest_version:
      latest_release = {
        'value': latest_release,
        'info': _("Your version is up-to-date."),
        'icon': 'cool'
      }
    else:
      latest_release = {
        'value': latest_release,
        'warning': _("Your version is newer than the latest release (?!?)"),
        'icon': 'confused'
      }
  else:
    latest_release = {
      'value': '?',
      'error': _("Version not found"),
      'icon': 'poop'
    }

  return latest_release


@login_required
def statistics(request):
  admin = Member.objects.filter(is_superuser=True).first()
  all_messages_count = ChatMessage.objects.count()
  public_chat_rooms = ChatRoom.objects.public()
  public_chat_messages_count = ChatMessage.objects.filter(room__in=public_chat_rooms).count()

  stats = {
    _('Site'): {
      _('Site name'): settings.SITE_NAME,
      _('Site URL'): request.build_absolute_uri('/'),
      _('Application Version'): settings.APP_VERSION,
      _('Latest release'): get_latest_release_text(request),
    },
    _('Members'): {
      _('Total number of members'): Member.objects.count(),
      _('Number of active members'): Member.objects.filter(is_active=True).count(),
      _('Number of managed members'): Member.objects.filter(is_active=False).count(),
    },
    _('Galleries'): {
      _('Number of galleries'): Gallery.objects.count(),
      _('Number of photos'): Photo.objects.count(),
    },
    _("Forums"): {
      _('Number of posts'): Post.objects.count(),
      _('Number of post messages'): Message.objects.count(),
      _('Number of message comments'): Comment.objects.count(),
    },
    _("Chats"): {
      _('Number of chat rooms'): ChatRoom.objects.count(),
      _('Number of public chat rooms'): ChatRoom.objects.public().count(),
      _('Number of private chat rooms'): PrivateChatRoom.objects.count(),
      _('Number of chat messages'): all_messages_count,
      _('Number of private chat messages'): all_messages_count - public_chat_messages_count,
      _('Number of public chat messages'): public_chat_messages_count,
    },
    _('Administrator'): {
      _('This site is managed by'): admin.full_name,
      _('Administrator email'): admin.email,
    },
  }
  return render(request, 'cm_main/about/site-stats.html', {'stats': stats})
