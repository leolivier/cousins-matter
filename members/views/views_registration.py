from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.views import generic

from ..registration_link_manager import RegistrationLinkManager
from tenants.models import Tenant
from tenants.scoping import tenant_context
from tenants.authz import admin_or_superusers
from tenants.services import resolve_join_tenant
from tenants.settings_overrides import tenant_setting
from ..forms import (
  MemberInvitationForm,
  RegistrationRequestForm,
  MemberRegistrationForm,
  AddressUpdateForm,
  FamilyUpdateForm,
)
from ..models import Member
from verify_email.email_handler import send_verification_email
from django.conf import settings
from core.mixins import LoginNotRequiredMixin


class RegistrationCheckingView(LoginNotRequiredMixin, generic.CreateView):
  title = _("Sign up")
  template_name = "members/members/member_upsert.html"

  def check_before_register(self, request, encoded_email, token):
    invitation_tenant_id, decoded_email = RegistrationLinkManager().decrypt_link(encoded_email, token)
    if not decoded_email:
      messages.error(request, _("Invalid link. Please contact the administrator."))
      return False
    # check if user is already logged in
    if request.user.is_authenticated:
      messages.error(request, _("You are already logged in"))
      return False
    # check if member is already registered
    member = Member.objects.filter(email=decoded_email)
    if member.exists():
      member = member.first()
      # if member is already active
      if member.is_active:
        messages.error(
          request,
          _("A member with the same email address is already active. Please sign in instead"),
        )
        return False
      # if member is already registered but is not active, ask him to contact his/her member manager
      manager = Member.objects.get(id=member.id).member_manager
      messages.error(
        request,
        _("You are already registered but not active. Please contact %(admin)s to activate your account")
        % {"admin": manager.full_name},
      )
      return False
    return True

  def get(self, request, encoded_email, token):
    if not self.check_before_register(request, encoded_email, token):
      return redirect("/")

    # Store invitation info in session for potential social login
    invitation_tenant_id, decoded_email = RegistrationLinkManager().decrypt_link(encoded_email, token)
    request.session["invitation_token"] = token
    request.session["invitation_email"] = decoded_email
    request.session["invitation_tenant_id"] = invitation_tenant_id

    return render(
      request,
      self.template_name,
      {
        "form": MemberRegistrationForm(),
        "addr_form": AddressUpdateForm(),
        "family_form": FamilyUpdateForm(),
        "title": self.title,
      },
    )

  def post(self, request, encoded_email, token):
    if not self.check_before_register(request, encoded_email, token):
      return redirect("/")

    form = MemberRegistrationForm(request.POST, request.FILES)

    if form.is_valid():
      # Create the new member on the invitation's tenant. The request is anonymous,
      # so the middleware hasn't set a current tenant; activate it explicitly.
      invitation_tenant_id = request.session.get("invitation_tenant_id")
      with tenant_context(Tenant(pk=invitation_tenant_id) if invitation_tenant_id else None):
        send_verification_email(request, form)  # also saves the member
      username = form.cleaned_data.get("username")
      messages.success(
        request,
        _(
          "Hello %(username)s, your account has been created! You will now receive an email "
          "to verify your email address. Click in the link inside the mail to finish the registration."
        )
        % {"username": username},
      )
      return redirect("members:login")

    return render(
      request,
      self.template_name,
      {
        "form": form,
        "addr_form": AddressUpdateForm(),
        "family_form": FamilyUpdateForm(),
        "title": self.title,
      },
    )


class MemberInvitationView(generic.View):
  template_name = "members/registration/registration_invite.html"

  def check_before_invitation(self, request):
    if not (request.user.is_superuser or request.user.is_tenant_admin or tenant_setting("allow_members_to_invite_members")):
      raise PermissionDenied(_("Only tenant admins can invite members"))

  def post(self, request):
    """
    Sends an email with a registration link to the user's email address.
    The self registration can be done only after receiving
    an invitation link from the admin. This link is sent to the user by email and contains a token.
    The user can then use the link to open the registration form and register.
    """
    ko = self.check_before_invitation(request)
    if ko:
      return ko
    form = MemberInvitationForm(request.POST)
    if not form.is_valid():
      messages.error(request, form.errors)
      return render(request, self.template_name, {"form": form})

    email = form.cleaned_data["email"]
    invited = form.cleaned_data["invited"]

    if Member.objects.filter(email=email).exists():
      messages.error(request, _("A member with this email already exists."))
      return render(request, self.template_name, {"form": form})

    invitation_url = RegistrationLinkManager().generate_link(request, email, tenant_id=request.user.tenant_id)
    site_name = tenant_setting("site_name")
    inviter = request.user
    admins = admin_or_superusers(request.user.tenant)
    admin = admins[0] if admins else inviter
    admin_name = admin.full_name
    from_email = settings.DEFAULT_FROM_EMAIL  # always use the default from email

    msg = render_to_string(
      "members/email/registration_invite_email.html",
      {
        "link": invitation_url,
        "admin": admin_name,
        "site_name": site_name,
        "invited": invited,
        "invited_email": email,
        "inviter": inviter.full_name,
        "inviter_email": inviter.email,
      },
      request=request,
    )

    send_mail(
      _("You are invited to register on %(site_name)s") % {"site_name": site_name},
      strip_tags(msg),
      from_email=from_email,
      recipient_list=[email],
      html_message=msg,
    )

    if admin != inviter:  # warn the admin if the inviter is not the admin
      msg = render_to_string(
        "members/email/registration_sent_email.html",
        {
          "admin": admin_name,
          "site_name": site_name,
          "invited": invited,
          "invited_email": email,
          "inviter": inviter.full_name,
          "inviter_email": inviter.email,
        },
        request=request,
      )
      send_mail(
        _("Invitation to register on %(site_name)s sent by %(inviter)s to %(invited)s")
        % {
          "site_name": site_name,
          "inviter": inviter.full_name,
          "inviter_email": inviter.email,
          "invited": invited,
          "invited_email": email,
        },
        strip_tags(msg),
        from_email=from_email,
        recipient_list=[admin.email],
        html_message=msg,
      )
    messages.success(request, _("Invitation sent to %(email)s.") % {"email": email})
    return render(request, self.template_name, {"form": form})

  def get(self, request):
    ko = self.check_before_invitation(request)
    if ko:
      return ko
    email = request.GET.get("mail")
    if email:
      form = MemberInvitationForm(initial={"email": email})
    else:
      form = MemberInvitationForm()
    return render(request, self.template_name, {"form": form})


class TenantJoinRequestView(LoginNotRequiredMixin, generic.View):
  """Anonymous request to join a family (captcha; routed to its admins).

  The tenant comes from the URL slug; the legacy ``members:register_request``
  alias and flag-off deployments resolve to the default tenant. The request is
  emailed to the tenant's admins (fallback: platform superusers) with a
  prefilled invitation link.
  """

  template_name = "members/registration/registration_request.html"

  THROTTLE_LIMIT = 5  # submissions per hour per IP, same policy as other
  THROTTLE_SECONDS = 3600  # anonymous public forms

  def get(self, request, slug=None):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      return render(request, self.template_name, {"form": RegistrationRequestForm()})

  def post(self, request, slug=None):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      form = RegistrationRequestForm(request.POST)
      if form.is_valid():
        if self._throttled(request):
          messages.error(request, _("Too many requests, please try again later."))
          return render(request, self.template_name, {"form": form})
        email = form.cleaned_data["email"]
        if Member.unscoped.filter(email=email).exists():
          # email login is global: an existing member can never re-claim it here
          messages.error(request, _("A member with this email already exists."))
          return render(request, self.template_name, {"form": form})
        if self._send_request(tenant, form.cleaned_data, request):
          messages.success(request, _("Registration request sent."))
          return redirect("tenant-home", slug=tenant.slug)
        messages.error(request, _("Unable to send mail, please contact your administrator"))
      return render(request, self.template_name, {"form": form})

  def _send_request(self, tenant, data, request) -> bool:
    """Render + send the request email to the tenant's admins. True on success."""
    site_name = tenant_setting("site_name")
    msg = render_to_string(
      "members/email/registration_request_email.html",
      {
        "site_name": site_name,
        "requester": {"email": data["email"], "name": data["name"], "message": data["message"]},
        "link": request.build_absolute_uri(reverse("members:invite")),
      },
      request=request,
    )
    admins = admin_or_superusers(tenant)
    if not admins:
      return False
    return (
      send_mail(
        _("Registration request for %(site_name)s") % {"site_name": site_name},
        strip_tags(msg),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin.email for admin in admins],
        html_message=msg,
      )
      == 1
    )

  def _throttled(self, request) -> bool:
    key = f"join-request:{request.META.get('REMOTE_ADDR', 'unknown')}"
    count = cache.get_or_set(key, 0, self.THROTTLE_SECONDS)
    if count >= self.THROTTLE_LIMIT:
      return True
    try:
      cache.incr(key)
    except ValueError:
      cache.set(key, 1, self.THROTTLE_SECONDS)
    return False
