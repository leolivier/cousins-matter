import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def check_followers(
  request,
  followed_object,
  followed_object_owner,
  followed_object_url,
  new_internal_object=None,
  author=None,
):
  """
  Sends an email to the followers of a followed object when a new element is added to it.
  Parameters:
  - request: the request object which triggered the change,
  - followed_object: the object that is followed (e.g. a chat room),
  - followed_object_owner: the member who owns the followed object,
  - new_internal_object: the just created object added to the followed object,
  - author is the member who created the new object,
  - followed_object_url is an url to display the followed object. If the request is not given (ie is None),
       then the followed_object_url must be an absolute URL, otherwise it has to be a relative URL.
  Followers are the members who follow the followed object, and they are stored in the followed_object.followers attribute.
  It is assumed that str(followed_object) returns a string that can be used as the name of the followed object.
  This method creates a task to execute the actual check asynchronously.
  """
  if request:  # otherwise, must be an absolute url!
    followed_object_url = request.build_absolute_uri(followed_object_url)

  async_task(
    "core.followers.do_check_followers",
    followed_object,
    followed_object_owner,
    followed_object_url,
    new_internal_object=new_internal_object,
    author=author,
    hook="core.followers.post_check_followers",
  )


def post_check_followers(task):
  logger.debug(f"post_check_followers: {task.result}")


def do_check_followers(
  followed_object,
  followed_object_owner,
  followed_object_url,
  new_internal_object=None,
  author=None,
):
  "see check_followers. Really implement the check"
  if new_internal_object is None:
    new_internal_object = followed_object

  # get all potential recipients (Member objects)
  recipients = set(followed_object.followers.all())
  if followed_object_owner:
    recipients.update(followed_object_owner.followers.all())
    recipients.add(followed_object_owner)
  if author:  # add author's followers to the list
    recipients.update(author.followers.all())

  logger.debug(f"recipients before author discard: {recipients}")
  # Filter out author and members who opted out of emails
  if author:
    recipients.discard(author)
  else:
    author = followed_object_owner
  logger.debug(f"recipients after author discard: {recipients}")

  immediate_recipients = []
  interested_count = 0

  from .models import NotificationEvent
  from members.models import Member

  for member in recipients:
    if member.email_batch_frequency == Member.FREQUENCY_NEVER:
      logger.debug(f"member {member} has email_batch_frequency == Member.FREQUENCY_NEVER")
      continue

    interested_count += 1
    if member.email_batch_frequency == Member.FREQUENCY_IMMEDIATE:
      logger.debug(f"member {member} has email_batch_frequency == Member.FREQUENCY_IMMEDIATE")
      immediate_recipients.append(member)
    else:
      # Store event for batching
      logger.debug(f"member {member} has email_batch_frequency == Member.FREQUENCY_BATCH")
      NotificationEvent.objects.create(
        member=member,
        followed_object=followed_object,
        new_object=new_internal_object,
        author=author,
        followed_object_url=followed_object_url,
      )

  obj_type = new_internal_object._meta.verbose_name
  obj_str = str(new_internal_object)
  follower_emails = [m.email for m in immediate_recipients if m.email]

  if interested_count == 0:
    logger.debug(f"{obj_type}:'{obj_str}' change is not interesting anyone")
    return 0
  else:
    logger.debug(
      f"""{obj_type}:'{obj_str}' change is interesting for {interested_count} people.
      Sending {len(immediate_recipients)} immediate emails."""
    )

  if not follower_emails:
    return 0

  return generate_emails(followed_object, followed_object_owner, new_internal_object, author, followed_object_url)


def generate_emails(followed_object, followed_object_owner, new_internal_object, author, followed_object_url, follower_emails):
  obj_type = new_internal_object._meta.verbose_name
  obj_str = str(new_internal_object)
  author_name = author.full_name
  followed_object_name = str(followed_object)
  if not followed_object_name:
    raise ValueError("followed object has no name")
  followed_type = followed_object._meta.verbose_name
  if followed_object == new_internal_object:  # it's a creation (eg a new post for followed members)
    title = _('New %(followed_type)s "%(followed_object_name)s"') % {
      "followed_type": followed_type,
      "followed_object_name": followed_object_name,
    }
    body = _('%(follower_name)s has created a new %(followed_type)s "%(followed_object_name)s"') % {
      "follower_name": author_name,
      "followed_type": followed_type,
      "followed_object_name": followed_object_name,
    }
  else:
    title = _('New %(obj_type)s added to %(followed_type)s "%(followed_object_name)s"') % {
      "obj_type": obj_type,
      "followed_object_name": followed_object_name,
      "followed_type": followed_type,
    }
    body = _('%(follower_name)s has added a new %(obj_type)s in the %(followed_type)s "%(followed_object_name)s"') % {
      "follower_name": author_name,
      "obj_type": obj_type,
      "followed_type": followed_type,
      "followed_object_name": followed_object_name,
    }

  email = EmailMultiAlternatives(
    title,
    body,
    settings.DEFAULT_FROM_EMAIL,
    [],
    bcc=follower_emails,
  )
  html_message = render_to_string(
    "core/followers/email-followers-on-change.html",
    {
      "title": title,
      "author_name": author_name,
      "creation": followed_object == new_internal_object,
      "obj_type": obj_type,
      "followed_type": followed_type,
      "followed_object_name": followed_object_name,
      "message": obj_str,
      "followed_object_url": followed_object_url,
    },
  )
  email.attach_alternative(html_message, "text/html")
  email.send()
  return len(follower_emails)


def toggle_follow(request, followed_object, owner, followed_object_url):
  """
  Toggles the follow status of a user for a given object and sends notifications.

  Parameters:
      request (HttpRequest): The HTTP request object containing user information.
      followed_object (Model): The object that the user is following or unfollowing.
      owner (User): The owner of the followed object.
      followed_object_url (str): The URL of the followed object.

  Raises:
      ValueError: If the followed object has no name.

  Returns:
      HttpResponseRedirect: Redirects to the followed object's URL.
  """

  followed_type = followed_object._meta.verbose_name
  if followed_object.followers.filter(id=request.user.id).exists():
    followed_object.followers.remove(request.user)
    messages.success(
      request,
      _("You are no longer following this %(followed_type)s") % {"followed_type": followed_type},
    )
  else:
    followed_object.followers.add(request.user)
    messages.success(
      request,
      _("You are now following this %(followed_type)s") % {"followed_type": followed_type},
    )
    # send email to author of followed object to tell him someone is following his object
    if owner and owner.id != request.user.id:  # don't send email to yourself or to nobody
      followed_url = request.build_absolute_uri(followed_object_url)
      follower_name = request.user.full_name
      followed_object_name = str(followed_object)
      if not followed_object_name:
        raise ValueError("followed object has no name")
      title = _('New follower to your %(followed_type)s "%(followed_object_name)s"') % {
        "followed_type": followed_type,
        "followed_object_name": followed_object_name,
      }
      message = _('%(follower_name)s is now following your %(followed_type)s "%(followed_object_name)s"') % {
        "follower_name": follower_name,
        "followed_type": followed_type,
        "followed_object_name": followed_object_name,
      }
      send_mail(
        title,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [owner.email],
        html_message=render_to_string(
          "core/followers/new_follower.html",
          {
            "follower_name": follower_name,
            "followed_type": followed_type,
            "followed_object_name": followed_object_name,
            "title": title,
            "followed_url": followed_url,
            "site_name": settings.SITE_NAME,
          },
        ),
      )
  return redirect(followed_object_url)
