from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views import generic
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from .models import Member, Address, Family
from .forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm
from accounts.forms import AccountUpdateForm, AccountRegisterForm
import logging

logger = logging.getLogger(__name__)

@login_required
def birthdays(request) -> HttpResponse:
  """
  Return the members with their birthday in the next ndays days
  (or previous ndays days if ndays <0)
  """
  ndays = 50 # TODO: parameterize
  today = date.today()
  deltaNdays = timedelta(days = ndays)
  bdays = []
  for m in Member.objects.all():
    nb = m.next_birthday()
    delta = nb - today
    if delta < deltaNdays:
        bdays.append((m, delta.days))
  context = {
    "birthdays_list": bdays,
    "ndays": ndays
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
    
@login_required
def view_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    # if this is not a GET, error
    if request.method != "GET":
        messages.error(request, _("Error: Only GET is allowed here"))
        return redirect("members:detail", kwargs={"pk":pk})

    m_form = MemberUpdateForm(instance=member)
    u_form = AccountUpdateForm(instance=member.account)

    return render(request, "members/member_detail.html", {"m_form": m_form,
                                                          "u_form": u_form, 
                                                          "pk":pk, 
                                                          "writable": False, 
                                                          "editable": editable(request, member),
                                                          "managing_account_name": managing_member_name(member)})

def upsert_member(request, member=None):
    """create or update a member"""
    # if we create a new member, if a user is logged in, he is creating a new managed member
    # otherwise, someone is self registering
    new_member = new_managed_member = self_registration = False
    if not member:
        new_member = True
        new_managed_member = request.user.is_authenticated
        self_registration = not new_managed_member

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request on existing member (or None):
        m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if self_registration:
            u_form = AccountRegisterForm(request.POST)
        elif new_managed_member: # no need of the passwords, we are creating an inactive account
            u_form = AccountUpdateForm(request.POST)
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

        account = u_form.save()

        if new_member:
            # if new member, it has been created by the account creation
            # retrieve it and recreate the member form with this instance
            member = Member.objects.get(account=account)
            m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
            # if new managed member is created, the associated account must be inactivated
            # and we force managing_account to the logged in user
            if new_managed_member:
                account.is_active = False
                account.save()
                member.managing_account = User.objects.get(id=request.user.id)
                member.save()

        member = m_form.save()

        # we should never go there!
        # if no managing account, we use the account if it's active otherwise the logged user account
        # if not member.managing_account:
        #     member.managing_account = account if account.is_active else User.objects.get(id=request.user.id)
        #     member.save()

        if self_registration:
            username = u_form.cleaned_data.get('username')
            messages.success(request, _('Hello %(username)s, your account has been created! You are now able to log in') % {"username": username})
            return redirect("accounts:login")
        elif new_managed_member:
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
        if self_registration:
            u_form = AccountRegisterForm()
        elif new_managed_member:
            u_form = AccountUpdateForm()
        else:
            u_form = AccountUpdateForm(instance=member.account)
        return render(request, "members/member_detail.html", {"m_form": m_form, "u_form": u_form, "pk":member.id if member else None,
                                                              "writable": editable(request, member),
                                                              "editable": editable(request, member),
                                                              "managing_account_name": managing_member_name(member)})


@login_required
def create_member(request):
    """creates a member"""
    # TODO: check if member already exists
    return upsert_member(request)

def register_member(request):
    """register a member, no login required"""
    # TODO: check if user is already logged in
    # TODO: check if user is already registered
    # TODO: check if user is already registered but not active
    # TODO: how to control self registration?
    return upsert_member(request)

@login_required
def change_member(request, pk=None):
    """change the member with id pk, to be used when the user is the managing account but not the account of the member"""
    # if pk, get existing member
    member = get_object_or_404(Member, pk=pk) if pk else None
    if member and member.account.id != request.user.id and member.managing_account.id!= request.user.id:
        messages.error(_("Error: You cannot change this member"))
        return redirect("members:detail", kwargs={"pk":pk})
    return upsert_member(request, member)

@login_required
def profile(request):
    """change the profile of the logged user (ie request.user.id = member.account.id)"""
    member = Member.objects.get(account__id=request.user.id)
    if member and member.account.id != request.user.id:
        messages.error(_("Error: Only cannot {first_name} {last_name} can change this member") \
                            % {"first_name": member.account.first_name, "last_name": member.account.last_name})
        return redirect("members:profile")
    return upsert_member(request, member)

@login_required
def activate_account(request, pk):
    """activate the account of the member with id pk"""
    member = get_object_or_404(Member, pk=pk)
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
        member.managing_account = member.account
        member.save()
        messages.success(request, _("Account successfully activated. The owner of the account must now proceed as if (s)he had lost his/her password before being able to log in."))
        logger.info("Account activated by %s" % request.user.username)

    logger.info("Request referer:  %s" % request.META['HTTP_REFERER'])
    return redirect(request.META['HTTP_REFERER'])