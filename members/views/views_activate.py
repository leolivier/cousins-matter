import logging
from base64 import urlsafe_b64encode

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.signing import SignatureExpired, BadSignature

from verify_email.email_handler import _VerifyEmail
from verify_email.token_manager import TokenManager as OriginalTokenManager
from verify_email.errors import InvalidToken, UserAlreadyActive, MaxRetriesExceeded, UserNotFound

from ..models import Member

logger = logging.getLogger(__name__)


class TokenManager(OriginalTokenManager):
  def generate_link(self, request, inactive_user, user_email):
    """
    Redefines generate_link to use another base URI and allow managing a different view in below class.
    """
    token = self.__generate_token(inactive_user)
    encoded_email = urlsafe_b64encode(str(user_email).encode('utf-8')).decode('utf-8')

    link = reverse("members:check_activation", args=[encoded_email, token])

    absolute_link = request.build_absolute_uri(link)
    return absolute_link


class VerifyEmail(_VerifyEmail):
    """
    Subclass of (normally hidden) _Verify email class
    Adds a send_activation_link method independantly of the member creation
    """
    def __init__(self):
      super().__init__()
      self.token_manager = TokenManager()

    def send_activation_link(self, request, member, email=None):
        """Sends an email to the member's email address with a link to verify the address.
            If email is not None, it will be used instead of the member's email address"""
        if member.is_active:
            raise UserAlreadyActive
        if not email:
            email = member.email
        member.is_active = False
        logger.info("User %s inactivated" % member.username)
        if email:
            member.email = email
        member.save()

        verification_url = self.token_manager.generate_link(request, member, member.email)
        msg = render_to_string(
            self.settings.get('html_message_template', raise_exception=True),
            {"link": verification_url, "inactive_user": member},
            request=request
        )

        self.__send_email(msg, member.email)
        logger.info(f"Activation link sent to {member.email} by {request.user.username}")
        return member


@login_required
def activate_member(request, pk):
    """activate the member with id pk"""
    member = get_object_or_404(Member, pk=pk)
    # TODO verify email
    if member.is_active:
      if member.managing_member is not None:
        member.managing_member = None
        member.save()
      messages.error(request, _("Error: Member already active"))
    elif not member.email:
        messages.error(request, _("Error: Member without email cannot be activated"))
    else:
        VerifyEmail().send_activation_link(request, member)
        messages.success(request,
                         _("Member account successfully activated. The owner of the account will now receive an email "
                           "containing an activation link then will be redirected to the password reset screen."))
        logger.info(f"Member {member.username} activated by {request.user.username}")

    return redirect(reverse("members:detail", args=[member.id]))


def check_activation(request, encoded_email, token):
  """check if the email verification is valid and activate the member if it is"""
  try:
    token_manager = TokenManager()
    member = token_manager.decrypt_link(encoded_email, token)
    if member:
      # if member is already active, redirect to login page
      if member.is_active:
        messages.error(
            request,
            _("A member with the same email address is already active. Please sign in instead")
        )
        return redirect(reverse("members:login"))
      else:
        # activate the member
        member.is_active = True
        member.managing_member = None
        member.save()
        # redirect to password set page
        uidb64 = urlsafe_base64_encode(force_bytes(member.pk))
        token = default_token_generator.make_token(member)
        reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
        messages.success(request,
                         _("Your email has been verified and your account is now activated. Please set your password."))
        return redirect(reset_url)

    else:
      # we dont know what went wrong...
      raise ValueError
  except (ValueError, TypeError) as error:
    logger.error(f'[ERROR]: Something went wrong while verifying user, exception: {error}')
    messages.error(request, _("Something went wrong while activating your account. Please try again."))
  except SignatureExpired:
    messages.error(request, _('The link has lived its life :( Request a new one!'))
  except BadSignature:
    messages.error(request, _('This link was modified before verification. <br>'
                              'Cannot request another verification link with faulty link.'))
  except MaxRetriesExceeded:
    messages.error(request, _('You have exceeded the maximum verification requests! Contact admin.'))
  except InvalidToken:
    messages.error(request, _('This link is invalid or been used already, we cannot verify using this link.'))
  except UserNotFound:
    raise Http404("404 User not found")

  return redirect(reverse("cm_main:Home"))
