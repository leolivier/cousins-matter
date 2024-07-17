
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from ..registration_link_manager import RegistrationLinkManager
from ..forms import (MemberInvitationForm, RegistrationRequestForm,
                     MemberRegistrationForm, AddressUpdateForm,
                     FamilyUpdateForm)
from cousinsmatter.utils import redirect_to_referer
from ..models import Member
from verify_email.email_handler import send_verification_email
from django.conf import settings


class RegistrationCheckingView(generic.CreateView):
  title = _("Sign up")
  template_name = "members/members/member_upsert.html"

  def check_before_register(self, request, encoded_email, token):
    decoded_email = RegistrationLinkManager().decrypt_link(encoded_email, token)
    if decoded_email:
      # check if user is already logged in
      if request.user.is_authenticated:
        messages.error(request, _("You are already logged in"))
        return redirect_to_referer(request)
      # check if member is already registered
      member = Member.objects.filter(email=decoded_email)
      if member.exists():
        member = member.first()
        # if member is already active, redirect to login page
        if member.is_active:
          messages.error(
            request,
            _("A member with the same email address is already active. Please sign in instead")
            )
          return redirect(reverse("members:login"))
        else:
          # if member is already registered but is not active, ask him to contact his/her managing member
          manager = Member.objects.get(id=member.id).managing_member
          messages.error(request,
                         _("You are already registered but not active. Please contact %(admin)s to activate your account") %
                         {'admin': manager.get_full_name()})
          return redirect_to_referer(request)
      return None
    else:
      return HttpResponseBadRequest(_("Invalid link. Please contact the administrator."))

  def get(self, request, encoded_email, token):
    checked_ko = self.check_before_register(request, encoded_email, token)
    if checked_ko:
      return checked_ko
    else:
      return render(request, self.template_name, {
          "form": MemberRegistrationForm(),
          "addr_form": AddressUpdateForm(),
          "family_form": FamilyUpdateForm(),
          "title": self.title,
      })

  def post(self, request, encoded_email, token):
    checked_ko = self.check_before_register(request, encoded_email, token)
    if checked_ko:
      return checked_ko

    form = MemberRegistrationForm(request.POST, request.FILES)

    if form.is_valid():
      send_verification_email(request, form)  # also saves the member
      username = form.cleaned_data.get('username')
      messages.success(
          request,
          _('Hello %(username)s, your account has been created! You will now receive an email '
            'to verify your email address. Click in the link inside the mail to finish the registration.') %
          {"username": username}
          )
      return redirect("members:login")

    return redirect_to_referer(request)


class MemberInvitationView(LoginRequiredMixin, generic.View):

  def post(self, request):
    """
    Sends an email with a registration link to the user's email address.
    The self registration can be done only after receiving
    an invitation link from the admin. This link is sent to the user by email and contains a token.
    The user can then use the link to open the registration form and register.
    """

    form = MemberInvitationForm(request.POST)
    if not form.is_valid():
      messages.error(request, form.errors)
      return redirect_to_referer(request)

    email = form.cleaned_data['email']
    invited = form.cleaned_data['invited']

    if Member.objects.filter(email=email).exists():
      messages.error(request, _('A member with this email already exists.'))
      return redirect_to_referer(request)

    invitation_url = RegistrationLinkManager().generate_link(request, email)
    site_name = settings.SITE_NAME
    inviter = request.user
    admin = Member.objects.filter(is_superuser=True).first()
    admin_name = admin.get_full_name()
    from_email = request.user.email

    msg = render_to_string(
      "members/email/registration_invite_email.html",
      {"link": invitation_url, "admin": admin_name, "site_name": site_name,
       "invited": invited, 'invited_email': email, 'inviter': inviter.get_full_name(),
       'inviter_email': inviter.email},
      request=request
    )

    send_mail(
      _("You are invited to register on %(site_name)s") % {'site_name': site_name}, strip_tags(msg),
      from_email=from_email,
      recipient_list=[email],
      html_message=msg
    )

    if admin != inviter:  # warn the admin if the inviter is not the admin
      msg = render_to_string(
        "members/email/registration_sent_email.html",
        {"admin": admin_name, "site_name": site_name, "invited": invited,
         'invited_email': email, 'inviter': inviter.get_full_name(),
         'inviter_email': inviter.email},
        request=request
      )
      send_mail(
        _("Invitation to register on %(site_name)s sent by %(inviter)s to %(invited)s") %
        {'site_name': site_name, 'inviter': inviter.get_full_name(), 'inviter_email': inviter.email,
         'invited': invited, 'invited_email': email},
        strip_tags(msg),
        from_email=from_email,
        recipient_list=[admin.email],
        html_message=msg
      )
    messages.success(request, _("Invitation sent to %(email)s.") % {'email': email})
    return redirect_to_referer(request)

  def get(self, request):
    email = request.GET.get('mail')
    if email:
      form = MemberInvitationForm(initial={'email': email})
    else:
      form = MemberInvitationForm()
    return render(request, "members/registration/registration_invite.html", {'form': form})


class RegistrationRequestView(generic.View):
  template_name = 'members/registration/registration_request.html'

  def post(self, request):
    """
    Allows a user to request a registration link.
    """
    form = RegistrationRequestForm(request.POST)
    # Validate the form: the captcha field will automatically
    # check the input
    if form.is_valid():  # Captcha OK

      site_name = settings.SITE_NAME
      requester_email = request.POST.get("email")
      if Member.objects.filter(email=requester_email).exists():
        messages.error(request, _('A member with this email already exists.'))
      else:
        requester_name = request.POST.get("name")
        requester_message = request.POST.get("message")
        link = reverse("members:invite")
        absolute_link = request.build_absolute_uri(link)

        context = {
          "site_name": site_name,
          "requester": {
            "email": requester_email,
            "name": requester_name,
            "message": requester_message
          },
          "link": absolute_link
        }

        msg = render_to_string("members/email/registration_request_email.html", context, request=request)
        admin = Member.objects.filter(is_superuser=True).first()
        if send_mail(
          _("Registration request for %(site_name)s") % {'site_name': site_name}, strip_tags(msg),
          from_email=settings.DEFAULT_FROM_EMAIL,
          recipient_list=[admin.email], html_message=msg
        ) == 1:
          messages.success(request, _("Registration request sent."))
          return redirect_to_referer(request)
        else:
          messages.error(request, _("Unable to send mail, please contact your administrator"))

    return render(request, self.template_name, {'form': form})

  def get(self, request):
    form = RegistrationRequestForm()
    return render(request, self.template_name, {'form': form})
