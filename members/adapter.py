import logging
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import Member
from .registration_link_manager import RegistrationLinkManager

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
  def pre_social_login(self, request, sociallogin):
    """
    Intervene after social auth but before account is created/connected.
    We check for an existing invited user in the session.
    """
    # 1. Look for email in social provider
    email = sociallogin.user.email
    if not email:
      messages.error(request, _("The identity provider did not provide an email address."))
      raise ImmediateHttpResponse(redirect("members:login"))

    # 2. Check if user already exists
    try:
      member = Member.objects.get(email=email)

      # If already active, just let them log in
      if member.is_active:
        return

      # Check for invitation in session
      ok, _tenant_id = self._check_invitation(request, email, clear=True)
      if ok:
        # Valid invitation found! Link and activate.
        sociallogin.connect(request, member)
        member.is_active = True
        member.save()
        logger.info(f"Member {member.username} activated via social login ({email})")
        return
      else:
        messages.error(
          request,
          _("This account is not yet active. Please use the invitation link sent to you by email."),
        )
        raise ImmediateHttpResponse(redirect("members:login"))

    except Member.DoesNotExist:
      # Case: No such member in DB yet.
      # If they have a valid invitation in session, we allow the signup.
      ok, tenant_id = self._check_invitation(request, email, clear=True)
      if ok:
        # Mark the new user as active so allauth creates it as such, and place
        # it on the invitation's tenant (the request is anonymous).
        sociallogin.user.is_active = True
        if tenant_id:
          sociallogin.user.tenant_id = tenant_id
        logger.info(f"New member signup allowed via social login with invitation ({email})")
        return
      else:
        messages.error(request, _("No invitation found for this email address. Please request an invitation first."))
        raise ImmediateHttpResponse(redirect("members:login"))

  def _check_invitation(self, request, email, clear=False):
    """Checks for a valid invitation for ``email`` in the session.

    Returns ``(ok, tenant_id)``: ``ok`` when the (email, tenant, token) triple
    validates; ``tenant_id`` is the invitation's tenant (or ``None``).
    """
    invitation_token = request.session.get("invitation_token")
    invitation_email = request.session.get("invitation_email")
    invitation_tenant_id = request.session.get("invitation_tenant_id")

    if invitation_token and invitation_email == email:
      if RegistrationLinkManager().check_invitation(email, invitation_tenant_id, invitation_token):
        if clear:
          request.session.pop("invitation_token", None)
          request.session.pop("invitation_email", None)
          request.session.pop("invitation_tenant_id", None)
        return True, invitation_tenant_id
    return False, None

  def list_providers(self, request):
    providers = super().list_providers(request)
    for p in providers:
      p.confirm_login = not settings.SOCIALACCOUNT_AUTO_SIGNUP
    return providers
