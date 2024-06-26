
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail


def check_followers(followed_object, new_internal_object, author, followed_object_url):
  """
    Sends an email to the followers of a followed object (followed_object) to which a new element new_internal_object is added.
    new_internal_object must be {'type': 'string'}, the type is used in the email subject and the value in the email body.
    e.g. new_internal_object = {'comment': 'This is a new comment'}
    author is the member who created the new object, and followed_object_url is an url to display the followed object.
    followers are the members who follow the followed object, and they are stored in the followed_object.followers attribute.
    It is assumed that str(followed_object) returns a string that can be used in the name of the followed object.
  """

  for obj_type, obj_str in new_internal_object.items():
    pass
  # don't send email to the author of the author
  follower_emails = [follower.email for follower in followed_object.followers.all() if follower.id != author.id]
  author_name = author.get_full_name()
  followed_object_name = str(followed_object)
  followed_type = followed_object._meta.verbose_name
  title = _('New %(obj_type)s added to %(followed_type)s "%(followed_object_name)s"') % {
                'obj_type': obj_type,
                'followed_object_name': followed_object_name,
                'followed_type': followed_type
              }
  email = EmailMultiAlternatives(
    title,
    _('%(follower_name)s has added a new %(obj_type)s in the %(followed_type)s "%(followed_object_name)s"') % {
                    'follower_name': author_name,
                    'obj_type': obj_type,
                    'followed_type': followed_type,
                    'followed_object_name': followed_object_name},
    settings.DEFAULT_FROM_EMAIL,
    [],
    bcc=follower_emails,
  )
  html_message = render_to_string('cm_main/followers/email-followers-on-change.html', {
    'title': title,
    'author_name': author_name,
    'obj_type': obj_type,
    'followed_type': followed_type,
    'followed_object_name': followed_object_name,
    'message': obj_str,
    'followed_object_url': followed_object_url
    })
  email.attach_alternative(html_message, "text/html")
  email.send()


# Base view function to toggle follow for a given object
def toggle_follow(request, followed_object, author, followed_object_url):

  followed_type = followed_object._meta.verbose_name
  if followed_object.followers.filter(id=request.user.id).exists():
    followed_object.followers.remove(request.user)
    messages.success(request, _(f"You are no longer following this {followed_type}"))
  else:
    followed_object.followers.add(request.user)
    messages.success(request, _(f"You are now following this {followed_type}"))
    # send email to author of followed object to tell him someone is following his object
    if author and author.id != request.user.id:  # don't send email to yourself or to nobody
      followed_url = request.build_absolute_uri(followed_object_url)
      follower_name = request.user.get_full_name()
      followed_object_name = str(followed_object)
      title = _('New follower to your %(followed_type)s "%(followed_object_name)s"') % {
        'followed_type': followed_type, 'followed_object_name': followed_object_name}
      message = _('%(follower_name)s is now following your %(followed_type)s "%(followed_object_name)s"') % {
        'follower_name': follower_name, 'followed_type': followed_type, 'followed_object_name': followed_object_name}
      send_mail(
        title,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [followed_object.first_message.author.email],
        html_message=render_to_string('cm_main/followers/new_follower.html', {
          'follower_name': follower_name,
          'followed_type': followed_type,
          'title': title,
          'followed_url': followed_url,
          'site_name': settings.SITE_NAME}),
      )
  return redirect(followed_object_url)
