import logging
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from verify_email.email_handler import _VerifyEmail
from ..models import Member

logger = logging.getLogger(__name__)

AccountAlreadyVerified = Exception("Account already verified")

# define a subclass of (normally hidden) _Verify email class
# to add a send_activation_link method indepentenly of the account creation
class VerifyEmail(_VerifyEmail):
    def send_activation_link(self, request, account, email=None):
        """Sends an email to the account's email address with a link to verify the address.
           If email is not None, it will be used instead of the account's email address"""
        if account.is_active:
            raise AccountAlreadyVerified()
        if not email: email = account.email
        account.is_active = False
        if email: account.email = email
        account.save()
        
        try:
            verification_url = self.token_manager.generate_link(request, account, account.email)
            msg = render_to_string(
                self.settings.get('html_message_template', raise_exception=True),
                {"link": verification_url, "inactive_user": account}, 
                request=request
            )

            self.__send_email(msg, account.email)
            return account
        except Exception:
            # account.delete()
            raise

@login_required
def activate_account(request, pk):
    """activate the account of the member with id pk"""
    member = get_object_or_404(Member, pk=pk)
    #TODO verify email
    if member.account.is_active:
        if member.managing_account != member.account:
            member.managing_account = member.account
            member.save()
        messages.error(request, _("Error: Account already active"))
    elif not member.account.email:
        messages.error(request, _("Error: Account without email cannot be activated"))
    else:
        member.account.is_active = True
        member.account.save()
        account = VerifyEmail().send_activation_link(request, member.account)
        member.managing_account = member.account
        member.save()
        messages.success(request, _("Account successfully activated. The owner of the account must now proceed as if (s)he had lost his/her password before being able to sign in."))
        logger.info("Account activated by %s" % request.user.username)

    logger.info("Request referer:  %s" % request.META['HTTP_REFERER'])
    return redirect(request.META['HTTP_REFERER'])

