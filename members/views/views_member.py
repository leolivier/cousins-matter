import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views import generic
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden, JsonResponse
from cm_main.utils import PageOutOfBounds, Paginator, remove_accents, assert_request_is_ajax
from verify_email.email_handler import send_verification_email
from ..models import Family, Member
from ..forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm

logger = logging.getLogger(__name__)


@login_required
def validate_username(request):
    """Check username availability"""
    username = request.GET.get('username', None)
    response = {
        'is_taken': username != request.user.username and Member.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(response)


@login_required
def validate_family_name(request):
    """Check family name availability"""
    family_name = request.GET.get('name', None)
    response = {
        'is_taken': Family.objects.filter(name__iexact=family_name).exists()
    }
    return JsonResponse(response)


@login_required
def logout_member(request):
    logout(request)
    messages.success(request, _("You have been logged out"))
    return redirect('members:login')


def editable(request, member):
    if request.user.is_superuser:
        return True
    manager = member.member_manager or member
    return manager.id == request.user.id


def member_manager_name(member):
    return Member.objects.get(id=member.member_manager.id).full_name if member and member.member_manager else None


class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members/members.html"
    # paginate_by = 100
    model = Member

    def get(self, request, page_num=1):
        members = Member.objects
        filters = {
            f'{name}_unaccent__icontains': remove_accents(request.GET[f'{name}_filter']).strip()
            for name in ['first_name', 'last_name']
            if request.GET.get(f'{name}_filter', '').strip()
        }
        members = members.filter(**filters) if filters else members.all()
        sort_by = request.GET.get('member_sort')
        order = '-' if request.GET.get('member_order') == 'option2' else ''  # default is ascending
        sort_by = [sort_by] if sort_by else ['last_name', 'first_name']  # default order
        sort_by = [order + s for s in sort_by]
        members = members.order_by(*sort_by)
        # print('sort by: ', sort_by, ' order: "', order, '" members query: ', members.query)
        try:
            page = Paginator.get_page(request,
                                      object_list=members,
                                      page_num=page_num,
                                      reverse_link='members:members_page',
                                      default_page_size=settings.DEFAULT_MEMBERS_PAGE_SIZE)
            return render(request, self.template_name, {"page": page})
        except PageOutOfBounds as exc:
            return redirect(exc.redirect_to)


class MemberDetailView(LoginRequiredMixin, generic.DetailView):
    model = Member
    template_name = "members/members/member_detail.html"

    def get_context_data(self, **kwargs):
        member = self.object
        return super().get_context_data(**kwargs) | \
          {
            "can_edit": editable(self.request, member),
            "member_manager_name": member.member_manager.username if member.member_manager else None,
            "hobbies_list": [s.strip() for s in member.hobbies.split(',')] if member.hobbies else [],
          }

    def get_absolute_url(self):
        return reverse("members:detail", kwargs={"pk": self.pk})


class CreateManagedMemberView(LoginRequiredMixin, generic.CreateView):
    """View used to create a managed member"""
    model = Member
    template_name = "members/members/member_upsert.html"

    def check_before_creation(self, request):
      if request.user.is_superuser or settings.ALLOW_MEMBERS_TO_CREATE_MEMBERS:
        return None
      return HttpResponseForbidden(_("Only superusers can create members"))

    def get(self, request, *args, **kwargs):
        ko = self.check_before_creation(request)
        if ko:
            return ko
        return render(request, self.template_name, {
            "form": MemberUpdateForm(),
            "addr_form": AddressUpdateForm(),
            "family_form": FamilyUpdateForm(),
            "title": _("Create Member"),
        })

    def post(self, request, *args, **kwargs):
        ko = self.check_before_creation(request)
        if ko:
            return ko
        form = MemberUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            # if new managed member is created, it must be inactivated
            member.is_active = False
            # force member_manager to the logged in user
            member.member_manager = Member.objects.get(id=request.user.id)
            member.save(update_fields=['is_active', 'member_manager'])
            messages.success(request, _('Member successfully created'))
            return redirect("members:detail", member.id)

        return render(request, self.template_name, {
            "form": form,
            "addr_form": AddressUpdateForm(),
            "family_form": FamilyUpdateForm(),
            "title": _("Create Member"),
        })


def _can_edit_member(request, member):
    if request.user.is_superuser:
        return True
    if member.member_manager is None:
        return (member.id == request.user.id)
    else:
        return (member.member_manager.id == request.user.id)


class EditMemberView(LoginRequiredMixin, generic.UpdateView):
    template_name = "members/members/member_upsert.html"
    title = _("Update Member Details")
    success_message = _("Member successfully updated")
    is_profile_view = False

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if not _can_edit_member(request, member):
            messages.error(request, _('You do not have permission to edit this member.'))
            return redirect("members:detail", member.id)

        return render(request, self.template_name, {
            "form": MemberUpdateForm(instance=member, is_profile=self.is_profile_view),
            "addr_form": AddressUpdateForm(),
            "family_form": FamilyUpdateForm(),
            "pk": pk,
            "title": self.title,
            "member_manager_name": member_manager_name(member)})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if not _can_edit_member(request, member):
            messages.error(request, _('You do not have permission to edit this member.'))
            return redirect("members:detail", member.id)

        # create a form instance and populate it with data from the request on existing member
        form = MemberUpdateForm(request.POST, request.FILES, instance=member, is_profile=self.is_profile_view)

        if form.is_valid():
            if member.id == request.user.id and 'email' in form.changed_data and form.cleaned_data['email']:
                # the member changed his own email, let's check it
                send_verification_email(request, form)
                messages.info(request, _("A verification email has been sent to validate your new email address."))
            else:
                form.save()
                messages.success(request, self.success_message)
            return redirect("members:detail", member.id)

        else:
            logger.error(f"u_form error: {form.errors}")
            return render(request, self.template_name, {
                "form": form,
                "addr_form": AddressUpdateForm(),
                "family_form": FamilyUpdateForm(),
                "pk": pk,
                "title": self.title,
                "member_manager_name": member_manager_name(member)})


class EditProfileView(EditMemberView):
    """change the profile of the logged user (ie request.user.id = member.id)"""
    template_name = "members/members/member_upsert.html"
    title = _("My Profile")
    success_message = _("Profile successfully updated")
    is_profile_view = True

    def get(self, request):
        return super().get(request, request.user.id)

    def post(self, request):
        return super().post(request, request.user.id)


def delete_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if not _can_edit_member(request, member):
        messages.error(request, _('You do not have permission to delete this member.'))
        return redirect("members:detail", member.id)
    member.delete()
    messages.info(request, _("Member deleted"))
    return redirect(reverse("members:members"))


@login_required
def search_members(request):
    assert_request_is_ajax(request)
    query = request.GET.get('q', '')
    members = Member.objects.filter(
        Q(last_name__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query.split()[-1]) |
        Q(first_name__icontains=query.split()[0])
    ).distinct()[:12]  # Limited to 12 results
    data = [{'id': m.id, 'text': m.full_name} for m in members]
    return JsonResponse({'results': data})
