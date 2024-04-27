import logging
from enum import Enum
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from verify_email.email_handler import send_verification_email
from ..models import Member
from ..forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm
from .utils import redirect_to_referer

from accounts.forms import AccountUpdateForm, AccountRegisterForm

logger = logging.getLogger(__name__)

MEMBER_MODE = Enum('MEMBER_MODE_ENUMS', ['create_managed', 'signup', 'update_managed', 'profile', 'show_details'])

def editable(request, member):
    return member.managing_account.id == request.user.id

def managing_member_name(member):
    return Member.objects.get(account__id=member.managing_account.id).get_full_name() if member else None

class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members.html"
    paginate_by = 100
    model = Member

class MemberDetailView(LoginRequiredMixin, generic.DetailView):
    model = Member

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | \
            { 
                "can_edit": editable(self.request, self.object),
                "managing_account_name": self.object.managing_account.username 
            }

def _update_member(request, mode:MEMBER_MODE, member=None):
    """display, create or update a member"""
 
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request on existing member (or None):
        m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if mode == MEMBER_MODE.signup:
            u_form = AccountRegisterForm(request.POST)
        elif mode == MEMBER_MODE.create_managed: # no need of the passwords, we are creating an inactive account
            u_form = AccountUpdateForm(request.POST)
        elif mode == MEMBER_MODE.show_details:
            messages.error(request, "Wrong mode: show_details in POST request")
            return redirect_to_referer(request)
        else: # we are updating an existing account
            u_form = AccountUpdateForm(request.POST, instance=member.account)

        if not u_form.is_valid() or not m_form.is_valid():
            messages.error(request, f"{_("Error")}: {u_form.errors} {m_form.errors}")
            try:
                logger.error(f">u_form instance {vars(u_form.instance)}\n{vars(u_form)}")
                logger.error(f">m_form instance {vars(m_form.instance)}\n{vars(m_form)}")
            except Exception as e:
                logger.error(f"error {e}")
            return redirect_to_referer(request)

        if  mode == MEMBER_MODE.signup or \
            (mode == MEMBER_MODE.profile and 'email' in u_form.changed_data):
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
            if mode == MEMBER_MODE.create_managed:
                account.is_active = False
                account.save()
                member.managing_account = User.objects.get(id=request.user.id)
                member.save()

        member = m_form.save()

        if mode == MEMBER_MODE.signup:
            username = u_form.cleaned_data.get('username')
            messages.success(request, _('Hello %(username)s, your account has been created! You will now receive an email to verify your email address. Click in the link inside the mail to finish the registration.') % {"username": username})
            return redirect("accounts:login")
        elif mode == MEMBER_MODE.create_managed:
            messages.success(request, _('Member successfully created'))
            return redirect("members:members")
        else:
            messages.success(request, _("Member successfully updated"))
            return redirect("members:members")

    # if a GET (or any other method) we'll create a "blank" form prefilled by existing member (or empty if member = None)
    else:
        m_form = MemberUpdateForm(instance=member)
        if mode == MEMBER_MODE.signup:
            u_form = AccountRegisterForm()
        elif mode == MEMBER_MODE.create_managed:
            u_form = AccountUpdateForm()
        else:
            u_form = AccountUpdateForm(instance=member.account)
        if member:
            a_form = AddressUpdateForm(instance=member.address)
            f_form = FamilyUpdateForm(instance=member.family)
        else:
            a_form = AddressUpdateForm()
            f_form = FamilyUpdateForm()
        return render(request, "members/member_upsert.html", {"m_form": m_form, "u_form": u_form, "addr_form": a_form, "family_form": f_form,
                                                              "pk":member.id if member else None,
                                                              "read_only": not editable(request, member),
                                                              "mode": mode.name,
                                                              "managing_account_name": managing_member_name(member)})


class CreateManagedMemberView(LoginRequiredMixin, generic.CreateView):
    """View used to create a managed member, and as a base class for other modes for the get part"""
    mode = MEMBER_MODE.create_managed
    template_name = "members/member_upsert.html"

    def get(self, request):
        return render(request, self.template_name, {
            "m_form": MemberUpdateForm(), 
            "u_form": AccountUpdateForm(), 
            "addr_form": AddressUpdateForm(), 
            "family_form": FamilyUpdateForm(),
            "mode": self.mode.name,
        })

    def post(self, request):
        # process the account first
        u_form = AccountUpdateForm(request.POST)
        if u_form.is_valid():
            # if new managed member is created, the associated account must be inactivated
            u_form.cleaned_data['is_active'] = False
            account = u_form.save()
            # account.is_active = False
            # account.save()
            # Now process the member which has been created by the account creation just above, through a signal
            # Retrieve it and recreate the member form with this instance
            if m_form.is_valid():
                # WARNING: as the creation is asynchronous, is the member always created here?
                member = Member.objects.get(account=account)
                # force managing_account to the logged in user
                member.managing_account = User.objects.get(id=request.user.id)
                # Create a form instance and populate it with data from the request on existing member (or None):
                m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
                member = m_form.save()
                messages.success(request, _('Member successfully created'))
                return redirect("members:detail", member.id)

        return redirect_to_referer(request)

class RegisterMemberView(CreateManagedMemberView):
    """register a member, accessible only through RegistrationCheckingView"""
    mode = MEMBER_MODE.signup

    def post(self, request):
        # start with account
        u_form = AccountRegisterForm(request.POST)

        if u_form.is_valid():
            account = send_verification_email(request, u_form)
            if m_form.is_valid():
                # if new member, it has been created by the account creation
                # retrieve it and recreate the member form with this instance
                member = Member.objects.get(account=account)
                m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
                member = m_form.save()

                username = u_form.cleaned_data.get('username')
                messages.success(request, _('Hello %(username)s, your account has been created! You will now receive an email to verify your email address. Click in the link inside the mail to finish the registration.') % {"username": username})
                return redirect("accounts:login")

        return redirect_to_referer(request)

class EditMemberView(LoginRequiredMixin, generic.UpdateView):
    template_name = "members/member_upsert.html"
    mode = MEMBER_MODE.update_managed

    def check_mode(self, request, member):
        """checks the MEMBER_MODE vs the context"""
        match self.mode:
            case MEMBER_MODE.update_managed:
                if member.account.id == request.user.id:
                    self.mode = MEMBER_MODE.profile # force profile mode
                elif member.managing_account.id != request.user.id:
                    messages.error(request, _(f"Only {managing_member_name(member)} is allowed to modify this member."))
                    return False
            case MEMBER_MODE.profile:
                if member.account.id != request.user.id:
                    messages.error(request, _(f"Wrong modification mode: {self.mode} with user id different of the connected person one"))
                    return False
            case _:
                messages.error(request, _(f"Wrong modification mode: {self.mode}"))
                return False
        
        return True

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)

        if not self.check_mode(request, member): return redirect_to_referer(request)

        return render(request, self.template_name, {
            "m_form": MemberUpdateForm(instance=member), 
            "u_form": AccountUpdateForm(instance=member.account), 
            "addr_form": AddressUpdateForm(instance=member.address), 
            "family_form": FamilyUpdateForm(instance=member.family),
            "pk":pk,
            "mode": self.mode.name,
            "managing_account_name": managing_member_name(member)})
    
    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if not self.check_mode(request, member): return redirect_to_referer(request)

        # create a form instance and populate it with data from the request on existing member
        m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        u_form = AccountUpdateForm(request.POST, instance=member.account)

        if u_form.is_valid():
            if self.mode == MEMBER_MODE.profile and 'email' in u_form.changed_data:
                # the member changed his own email, let's check it
                send_verification_email(request, u_form)
                messages.info(request, _("A verification email has been sent to validate your new email address."))
            else:
                u_form.save()

            if m_form.is_valid():
                member = m_form.save()
                messages.success(request, _("Member successfully updated"))
                return redirect("members:detail", member.id)

        return redirect_to_referer(request)

class EditProfileView(EditMemberView):
    """change the profile of the logged user (ie request.user.id = member.account.id)"""
    mode = MEMBER_MODE.profile

    def get(self, request):
        return super().get(request, request.user.id)
    
    def post(self, request):
        return super().post(request, request.user.id)

