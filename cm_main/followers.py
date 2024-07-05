
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail

from cousinsmatter.utils import get_absolute_url_wo_request

logger = logging.getLogger(__name__)


def check_followers(request, followed_object, followed_object_owner, followed_object_url, 
                    new_internal_object=None, author=None):
  """
    Sends an email to the followers of a followed object (followed_object) to which a new element new_internal_object is added.
    new_internal_object is the just create object, 
    author is the member who created the new object, and followed_object_url is an url to display the followed object.
    followers are the members who follow the followed object, and they are stored in the followed_object.followers attribute.
    It is assumed that str(followed_object) returns a string that can be used in the name of the followed object.
  """
  if new_internal_object is None:
    new_internal_object = followed_object
  if author is None:
    author = followed_object_owner

  obj_type = new_internal_object._meta.verbose_name
  obj_str = str(new_internal_object)
  # get the emails of the followers of the followed object except the author of the new object
  follower_emails = [follower.email for follower in followed_object.followers.all() if follower.id != author.id]
  logger.debug('follower email:', follower_emails)
  # also send emails to the followers of the owner
  follower_emails += [follower.email for follower in followed_object_owner.followers.all()]
  logger.debug('follower email + owner followers emails:', follower_emails)
  # and also to the owner (he is an implicit follower of his own objects)
  follower_emails.append(followed_object_owner.email)
  logger.debug('follower email + owner:', follower_emails)
  # remove duplicates
  follower_emails = list(set(follower_emails))
  # remove empty emails or None emails
  follower_emails = [email for email in follower_emails if email]

  if len(follower_emails) == 0:
    logger.debug(f"{obj_type}:'{obj_str}' change is not interesting anyone")
    return
  else:
    logger.debug(f"{obj_type}:'{obj_str}' change is interesting for {len(follower_emails)} people: {follower_emails}")

  author_name = author.get_full_name()
  followed_object_name = str(followed_object)
  followed_object_url = request.build_absolute_uri(followed_object_url) if request \
    else get_absolute_url_wo_request(followed_object_url)
  if not followed_object_name:
    raise ValueError('followed object has no name')
  followed_type = followed_object._meta.verbose_name
  if followed_object == new_internal_object:  # it's a creation (eg a new post for followed members)
    title = _('New %(followed_type)s "%(followed_object_name)s"') % {
      'followed_type': followed_type,
      'followed_object_name': followed_object_name
      }
    body = _('%(follower_name)s has created a new %(followed_type)s "%(followed_object_name)s"') % {
                    'follower_name': author_name,
                    'followed_type': followed_type,
                    'followed_object_name': followed_object_name}
  else:
    title = _('New %(obj_type)s added to %(followed_type)s "%(followed_object_name)s"') % {
                'obj_type': obj_type,
                'followed_object_name': followed_object_name,
                'followed_type': followed_type
              }
    body = _('%(follower_name)s has added a new %(obj_type)s in the %(followed_type)s "%(followed_object_name)s"') % {
                    'follower_name': author_name,
                    'obj_type': obj_type,
                    'followed_type': followed_type,
                    'followed_object_name': followed_object_name}

  email = EmailMultiAlternatives(
    title,
    body,
    settings.DEFAULT_FROM_EMAIL,
    [],
    bcc=follower_emails,
  )
  html_message = render_to_string('cm_main/followers/email-followers-on-change.html', {
    'title': title,
    'author_name': author_name,
    'creation': followed_object == new_internal_object,
    'obj_type': obj_type,
    'followed_type': followed_type,
    'followed_object_name': followed_object_name,
    'message': obj_str,
    'followed_object_url': followed_object_url
    })
  email.attach_alternative(html_message, "text/html")
  email.send()


# Base view function to toggle follow for a given object
def toggle_follow(request, followed_object, owner, followed_object_url):

  followed_type = followed_object._meta.verbose_name
  if followed_object.followers.filter(id=request.user.id).exists():
    followed_object.followers.remove(request.user)
    messages.success(request, _(f"You are no longer following this {followed_type}"))
  else:
    followed_object.followers.add(request.user)
    messages.success(request, _(f"You are now following this {followed_type}"))
    # send email to author of followed object to tell him someone is following his object
    if owner and owner.id != request.user.id:  # don't send email to yourself or to nobody
      followed_url = request.build_absolute_uri(followed_object_url)
      follower_name = request.user.get_full_name()
      followed_object_name = str(followed_object)
      if not followed_object_name:
        raise ValueError('followed object has no name')
      title = _('New follower to your %(followed_type)s "%(followed_object_name)s"') % {
        'followed_type': followed_type, 'followed_object_name': followed_object_name}
      message = _('%(follower_name)s is now following your %(followed_type)s "%(followed_object_name)s"') % {
        'follower_name': follower_name, 'followed_type': followed_type, 'followed_object_name': followed_object_name}
      send_mail(
        title,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [owner.email],
        html_message=render_to_string('cm_main/followers/new_follower.html', {
          'follower_name': follower_name,
          'followed_type': followed_type,
          'followed_object_name': followed_object_name,
          'title': title,
          'followed_url': followed_url,
          'site_name': settings.SITE_NAME}),
      )
  return redirect(followed_object_url)
