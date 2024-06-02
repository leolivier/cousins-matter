import logging
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from verify_email.email_handler import send_verification_email
from ..models import Member
from ..forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm
from cousinsmatter.utils import redirect_to_referer
from accounts.forms import AccountUpdateForm

logger = logging.getLogger(__name__)


def editable(request, member):
    return member.managing_account.id == request.user.id


def managing_member_name(member):
    return Member.objects.get(account__id=member.managing_account.id).get_full_name() if member else None


class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members.html"
    # paginate_by = 100
    model = Member

    def get(self, request):
        filter = {}
        if 'first_name_filter' in request.GET and request.GET['first_name_filter']:
            filter['account__first_name__icontains'] = request.GET['first_name_filter']
        if 'last_name_filter' in request.GET and request.GET['last_name_filter']:
            filter['account__last_name__icontains'] = request.GET['last_name_filter']
        logger.debug("filter:", filter)
        members = Member.objects.filter(**filter)
        return render(request, self.template_name, {"member_list": members})


class MemberDetailView(LoginRequiredMixin, generic.DetailView):
    model = Member

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | \
            {
                "can_edit": editable(self.request, self.object),
                "managing_account_name": self.object.managing_account.username,
                "hobbies_list": [s.strip() for s in self.object.hobbies.split(',')] if self.object.hobbies else [],
            }

    def get_absolute_url(self):
        return reverse("members:detail", kwargs={"pk": self.pk})


class CreateManagedMemberView(LoginRequiredMixin, generic.CreateView):
    """View used to create a managed member"""
    model = Member

    template_name = "members/member_upsert.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "m_form": MemberUpdateForm(),
            "u_form": AccountUpdateForm(),
            "addr_form": AddressUpdateForm(),
            "family_form": FamilyUpdateForm(),
            "title": _("Create Member"),
        })

    def post(self, request, *args, **kwargs):
        # process the account first
        u_form = AccountUpdateForm(request.POST)
        if u_form.is_valid():
            account = u_form.save()
            # if new managed member is created, the associated account must be inactivated
            account.is_active = False
            account.save()

            # Now process the member which has been created by the account creation just above, through a signal
            # Retrieve it and recreate the member form with this instance
            # WARNING: as the creation is asynchronous, is the member always created here?
            member = Member.objects.get(account=account)
            # force managing_account to the logged in user
            member.managing_account = User.objects.get(id=request.user.id)
            # Create a form instance and populate it with data from the request on existing member (or None):
            m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
            if m_form.is_valid():
                member = m_form.save()
                messages.success(request, _('Member successfully created'))
                return redirect("members:detail", member.id)

        return redirect_to_referer(request)


class EditMemberView(LoginRequiredMixin, generic.UpdateView):
    template_name = "members/member_upsert.html"
    title = _("Update Member Details")
    success_message = _("Member successfully updated")

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if member.managing_account.id != request.user.id:
            messages.error(request, _('You do not have permission to edit this member.'))
            return redirect("members:detail", member.id)

        # force profile mode
        if member.account.id == request.user.id:
            self.title = _("My Profile")

        return render(request, self.template_name, {
            "m_form": MemberUpdateForm(instance=member),
            "u_form": AccountUpdateForm(instance=member.account),
            "addr_form": AddressUpdateForm(instance=member.address),
            "family_form": FamilyUpdateForm(instance=member.family),
            "pk": pk,
            "title": self.title,
            "managing_account_name": managing_member_name(member)})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if member.managing_account.id != request.user.id:
            messages.error(request, _('You do not have permission to edit this member.'))
            return redirect("members:detail", member.id)

        # create a form instance and populate it with data from the request on existing member
        m_form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        u_form = AccountUpdateForm(request.POST, instance=member.account)

        if u_form.is_valid():
            if member.account.id == request.user.id and 'email' in u_form.changed_data and u_form.cleaned_data['email']:
                # the member changed his own email, let's check it
                send_verification_email(request, u_form)
                messages.info(request, _("A verification email has been sent to validate your new email address."))
            else:
                u_form.save()

            if m_form.is_valid():
                member = m_form.save()
                messages.success(request, self.success_message)
                return redirect("members:detail", member.id)

            else:
                logger.error(f"m_form error: {m_form.errors}")

        else:
            logger.error(f"u_form error: {u_form.errors}")

        return redirect_to_referer(request)


class EditProfileView(EditMemberView):
    """change the profile of the logged user (ie request.user.id = member.account.id)"""
    title = _("My Profile")
    success_message = _("Profile successfully updated")

    def get(self, request):
        member = Member.objects.get(account_id=request.user.id)
        return super().get(request, member.id)

    def post(self, request):
        member = Member.objects.get(account_id=request.user.id)
        return super().post(request, member.id)
