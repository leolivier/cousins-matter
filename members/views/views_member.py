import logging
from urllib.parse import urlencode
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views import generic
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.http import JsonResponse
from cousinsmatter.utils import Paginator
from verify_email.email_handler import send_verification_email
from cousinsmatter.utils import redirect_to_referer
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
    manager = member.managing_member or member
    return manager.id == request.user.id


def managing_member_name(member):
    return Member.objects.get(id=member.managing_member.id).get_full_name() if member and member.managing_member else None


class MembersView(LoginRequiredMixin, generic.ListView):
    template_name = "members/members.html"
    # paginate_by = 100
    model = Member

    def get(self, request, page_num=1):
        filter = {}
        if 'first_name_filter' in request.GET and request.GET['first_name_filter']:
            filter['first_name__icontains'] = request.GET['first_name_filter']
        if 'last_name_filter' in request.GET and request.GET['last_name_filter']:
            filter['last_name__icontains'] = request.GET['last_name_filter']
        members = Member.objects.filter(**filter)
        # filter = []
        # query = 'SELECT * from members_member WHERE '
        # if 'first_name_filter' in request.GET and request.GET['first_name_filter']:
        #     filter.append(globalize_for_search(request.GET['first_name_filter']))
        #     query += 'first_name GLOB %s '
        # if 'last_name_filter' in request.GET and request.GET['last_name_filter']:
        #     filter.append(globalize_for_search(request.GET['last_name_filter']))
        #     query += 'last_name GLOB %s '

        # if len(filter) > 0:
        #     members = Member.objects.raw(query, filter)
        #     logger.info("query:", query, "filter: ", filter, 'count', members.count())
        # else:
        #     members = Member.objects.all()
        page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_MEMBERS_PAGE_SIZE
        # print("page_size=", page_size)
        ptor = Paginator(members, page_size, reverse_link='members:members_page')
        if page_num > ptor.num_pages:
            return redirect(reverse('members:members_page', args=[ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
        page = ptor.get_page_data(page_num)
        return render(request, self.template_name, {"page": page})


class MemberDetailView(LoginRequiredMixin, generic.DetailView):
    model = Member

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

    template_name = "members/member_upsert.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "form": MemberUpdateForm(),
            "addr_form": AddressUpdateForm(),
            "family_form": FamilyUpdateForm(),
            "title": _("Create Member"),
        })

    def post(self, request, *args, **kwargs):
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
    template_name = "members/member_upsert.html"
    title = _("Update Member Details")
    success_message = _("Member successfully updated")

    def _can_edit(self, request, member):
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
            "form": MemberUpdateForm(instance=member),
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
        form = MemberUpdateForm(request.POST, request.FILES, instance=member)

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
    title = _("My Profile")
    success_message = _("Profile successfully updated")

    def get(self, request):
        return super().get(request, request.user.id)

    def post(self, request):
        return super().post(request, request.user.id)


def delete_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    member.delete()
    return redirect(reverse("members:members"))
