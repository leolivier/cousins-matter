import logging
from enum import Enum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse
from django.views import generic
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from verify_email.email_handler import send_verification_email, _VerifyEmail
from .models import Member, Address, Family
from .forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm
from accounts.forms import AccountUpdateForm, AccountRegisterForm
from cousinsmatter import settings 

logger = logging.getLogger(__name__)

MEMBER_MODE_ENUMS = Enum('MEMBER_MODE_ENUMS', ['create_managed', 'signup', 'update_managed', 'profile', 'show_details'])

@login_required
def birthdays(request) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAYS_NDAYS days
  (or previous settings.BIRTHDAYS_NDAYS days if settings.BIRTHDAYS_NDAYS <0)
  """
  today = date.today()
  deltaNdays = timedelta(days = settings.BIRTHDAYS_NDAYS)
  bdays = []
  for m in Member.objects.all():
    nb = m.next_birthday()
    delta = nb - today
    if delta < deltaNdays:
        bdays.append((m, delta.days))
  context = {
    "birthdays_list": bdays,
    "ndays": settings.BIRTHDAYS_NDAYS
  }
  return render(request, "members/birthdays.html", context)

class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members.html"
    model = Member

@login_required
class MemberView(generic.DetailView):
   model = Member


def editable(request, member):
    # res = member and member.managing_account.id == request.user.id
    # print(f"editable: {res} user id={request.user.id}\nmember = {vars(member)} ")
    return (not member) or member.managing_account.id == request.user.id

def managing_member_name(member):
    if member:
        managing_member = Member.objects.filter(account__id=member.managing_account.id)
        if managing_member:
            return managing_member.first().__str__()
        return member.managing_account.username
    else:
        return None

def _view_member(request, mode:MEMBER_MODE_ENUMS, member=None):
    """display, create or update a member"""
 
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request on existing member (or None):
        m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if mode == MEMBER_MODE_ENUMS.signup:
            u_form = AccountRegisterForm(request.POST)
        elif mode == MEMBER_MODE_ENUMS.create_managed: # no need of the passwords, we are creating an inactive account
            u_form = AccountUpdateForm(request.POST)
        elif mode == MEMBER_MODE_ENUMS.show_details:
            messages.error(request, "Wrong mode: show_details in POST request")
            return redirect("Home")
        else: # we are updating an existing account
            u_form = AccountUpdateForm(request.POST, instance=member.account)

        if not u_form.is_valid() or not m_form.is_valid():
            messages.error(request, f"{_("Error")}: {u_form.errors} {m_form.errors}")
            try:
                logger.error(f">u_form instance {vars(u_form.instance)}\n{vars(u_form)}")
                logger.error(f">m_form instance {vars(m_form.instance)}\n{vars(m_form)}")
            except Exception as e:
                logger.error(f"error {e}")
            return redirect("Home")

        if  mode == MEMBER_MODE_ENUMS.signup or \
            (mode == MEMBER_MODE_ENUMS.profile and u_form.data.email != member.account.email):
            # the returned account is inactive and saved
            account = send_verification_email(request, u_form)
        else:
            account = u_form.save()

        if not member:
            # if new member, it has been created by the account creation
            # retrieve it and recreate the member form with this instance
            member = Member.objects.get(account=account)
            m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
            # if new managed member is created, the associated account must be inactivated
            # and we force managing_account to the logged in user
            if mode == MEMBER_MODE_ENUMS.create_managed:
                account.is_active = False
                account.save()
                member.managing_account = User.objects.get(id=request.user.id)
                member.save()

        member = m_form.save()

        if mode == MEMBER_MODE_ENUMS.signup:
            username = u_form.cleaned_data.get('username')
            messages.success(request, _('Hello %(username)s, your account has been created! You will now receive an email to verify your email address. Click in the link inside the mail to finish the registration.') % {"username": username})
            return redirect("accounts:login")
        elif mode == MEMBER_MODE_ENUMS.create_managed:
            messages.success(request, _('Member successfully created'))
            return redirect("members:members")
        else:
            messages.success(request, _("Member successfully updated"))
            # if u_form.instance.id == request.user.id:
            #     return redirect("members:profile")
            # else:
            #     return redirect("members:detail", args=(member.id,))
            return redirect("members:members")

    # if a GET (or any other method) we'll create a "blank" form prefilled by existing member (or empty if member = None)
    else:
        m_form = MemberUpdateForm(instance=member)
        if mode == MEMBER_MODE_ENUMS.signup:
            u_form = AccountRegisterForm()
        elif mode == MEMBER_MODE_ENUMS.create_managed:
            u_form = AccountUpdateForm()
        else:
            u_form = AccountUpdateForm(instance=member.account)
        
        return render(request, "members/member_detail.html", {"m_form": m_form, "u_form": u_form, "pk":member.id if member else None,
                                                              "read_only": not editable(request, member),
                                                              "mode": mode.name,
                                                              "managing_account_name": managing_member_name(member)})


@login_required
def create_member(request):
    """creates a member"""
    # TODO: check if member already exists
    return _view_member(request, MEMBER_MODE_ENUMS.create_managed)

def register_member(request):
    """register a member, no login required"""
    # check if user is already logged in
    if request.user.is_authenticated:
        messages.error(request, _("You are already logged in"))
        return redirect("Home")
    # check if member is already registered
    account = User.objects.filter(email=request.POST.get("email"))
    if not account.exists():
        account = User.objects.filter(email=request.POST.get("username"))
    if account.exists():
        account = account.first()
        # if member is already registered but account not active, ask him to contact his/her managing account
        if account.is_active:
            messages.error(request, _("A member with the same account name or email address is already registered. Please login instead"))
            return redirect("Home")
        else:
            manager = Member.objects.get(account__id=account.id).managing_account
            messages.error(request, _("You are already registered but not active. Please contact %s to activate your account") % manager.member.get_full_name())
            return redirect("Home")
    # TODO: how to control self registration by an admin?
    return _view_member(request, MEMBER_MODE_ENUMS.signup)

@login_required
def display_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if member.account.id == request.user.id:
        mode = MEMBER_MODE_ENUMS.profile
    elif member.managing_account.id == request.user.id:
        mode = MEMBER_MODE_ENUMS.update_managed
    else:
        mode = MEMBER_MODE_ENUMS.show_details
    return _view_member(request, mode, member)

@login_required
def profile(request):
    """change the profile of the logged user (ie request.user.id = member.account.id)"""
    member = Member.objects.get(account__id=request.user.id)
    if member and member.account.id != request.user.id:
        messages.error(_("Error: Only cannot {first_name} {last_name} can change this member") \
                            % {"first_name": member.account.first_name, "last_name": member.account.last_name})
        return redirect("members:profile")
    return _view_member(request, MEMBER_MODE_ENUMS.profile, member)

AccountAlreadyVerified = Exception("Account already verified")
class VerifyEmail(_VerifyEmail):
    def send_activation_link(self, request, account, email=None):
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
        messages.success(request, _("Account successfully activated. The owner of the account must now proceed as if (s)he had lost his/her password before being able to log in."))
        logger.info("Account activated by %s" % request.user.username)

    logger.info("Request referer:  %s" % request.META['HTTP_REFERER'])
    return redirect(request.META['HTTP_REFERER'])