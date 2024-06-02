import logging
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from verify_email.email_handler import _VerifyEmail
from cousinsmatter.utils import redirect_to_referer
from ..models import Member

logger = logging.getLogger(__name__)

AccountAlreadyVerified = Exception("Account already verified")


class VerifyEmail(_VerifyEmail):
    """
    Subclass of (normally hidden) _Verify email class
    Adds a send_activation_link method independantly of the member creation
    """
    def send_activation_link(self, request, member, email=None):
        """Sends an email to the member's email address with a link to verify the address.
            If email is not None, it will be used instead of the member's email address"""
        if member.is_active:
            raise AccountAlreadyVerified()
        if not email:
            email = member.email
        member.is_active = False
        logger.info("User %s inactivated" % member.username)
        if email:
            member.email = email
        member.save()

        try:
            verification_url = self.token_manager.generate_link(request, member, member.email)
            msg = render_to_string(
                self.settings.get('html_message_template', raise_exception=True),
                {"link": verification_url, "inactive_user": member},
                request=request
            )

            self.__send_email(msg, member.email)
            logger.info(f"Activation link sent to {member.email} by {request.user.username}")
            return member
        except Exception:
            # member.delete()
            raise


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
        member.is_active = True
        member.save()
        VerifyEmail().send_activation_link(request, member)
        member.managing_member = None
        member.save()
        messages.success(request,
                         _("Member account successfully activated. The owner of the account must now proceed as if (s)he had lost his/her password before being able to sign in."))  # noqa: E501
        logger.info(f"Member {member.username} activated by {request.user.username}")

    return redirect_to_referer(request)
