import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Q, F, Func
from django.urls import reverse
from django.views import generic
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden, JsonResponse
from cousinsmatter.utils import Paginator, remove_accents
from verify_email.email_handler import send_verification_email
from cousinsmatter.utils import assert_request_is_ajax, redirect_to_referer
from ..models import Member
from ..forms import MemberUpdateForm, AddressUpdateForm, FamilyUpdateForm

logger = logging.getLogger(__name__)


def validate_username(request):
    """Check username availability"""
    username = request.GET.get('username', None)
    response = {
        'is_taken': username != request.user.username and Member.objects.filter(username__iexact=username).exists()
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
    manager = member.managing_member or member
    return manager.id == request.user.id


def managing_member_name(member):
    return Member.objects.get(id=member.managing_member.id).full_name if member and member.managing_member else None


def register_remove_accents():
    # Execute this if database is SQLite only, and only once
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
      from django.db import connection
      # Register custom function in the database
      with connection.cursor() as cursor:
        cursor.connection.create_function('REMOVE_ACCENTS', 1, remove_accents)


class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members/members.html"
    # paginate_by = 100
    model = Member

    def get(self, request, page_num=1):
        register_remove_accents()
        filtered = False
        members = Member.objects
        for name in ['first_name', 'last_name']:
            name_filter = name + '_filter'
            if name_filter in request.GET and request.GET[name_filter]:
                # issue #149: strip leading and trailing spaces on first and last name of filter
                normalized_name = remove_accents(request.GET[name_filter].strip())
                members = members.annotate(
                    normalized_name=Func(F(name), function='REMOVE_ACCENTS')).filter(
                    normalized_name__icontains=normalized_name)
                filtered = True
        if not filtered:
            members = members.all()
        members = members.order_by('last_name', 'first_name')
        page = Paginator.get_page(request,
                                  object_list=members,
                                  page_num=page_num,
                                  reverse_link='members:members_page',
                                  default_page_size=settings.DEFAULT_MEMBERS_PAGE_SIZE)
        return render(request, self.template_name, {"page": page})


class MemberDetailView(LoginRequiredMixin, generic.DetailView):
    model = Member
    template_name = "members/members/member_detail.html"

    def get_context_data(self, **kwargs):
        member = self.object
        return super().get_context_data(**kwargs) | \
          {
            "can_edit": editable(self.request, member),
            "managing_member_name": member.managing_member.username if member.managing_member else None,
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
            # force managing_member to the logged in user
            member.managing_member = Member.objects.get(id=request.user.id)
            member.save(update_fields=['is_active', 'managing_member'])
            messages.success(request, _('Member successfully created'))
            return redirect("members:detail", member.id)

        return redirect_to_referer(request)


class EditMemberView(LoginRequiredMixin, generic.UpdateView):
    template_name = "members/members/member_upsert.html"
    title = _("Update Member Details")
    success_message = _("Member successfully updated")
    is_profile_view = False

    def _can_edit(self, request, member):
        if request.user.is_superuser:
            return True
        if member.managing_member is None:
            return (member.id == request.user.id)
        else:
            return (member.managing_member.id == request.user.id)

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if not self._can_edit(request, member):
            messages.error(request, _('You do not have permission to edit this member.'))
            return redirect("members:detail", member.id)

        return render(request, self.template_name, {
            "form": MemberUpdateForm(instance=member, is_profile=self.is_profile_view),
            "addr_form": AddressUpdateForm(instance=member.address),
            "family_form": FamilyUpdateForm(instance=member.family),
            "pk": pk,
            "title": self.title,
            "managing_member_name": managing_member_name(member)})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if not self._can_edit(request, member):
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
            return redirect_to_referer(request)


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
