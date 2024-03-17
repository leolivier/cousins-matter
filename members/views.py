from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from .models import Member, Address, Family
from .forms import MemberUpdateForm, MemberUpdateNoAccountForm, AddressUpdateForm, FamilyUpdateForm
from accounts.forms import AccountUpdateForm
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
    if request.user.is_superuser:
        return True
    elif member:
        return member.managing_account.id == request.user.id
    else:
        return False

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
    # if this is not a GET, error
    if request.method != "GET":
        return HttpResponse("Error: Only GET is allowed here")

    member = get_object_or_404(Member, pk=pk)

    form = MemberUpdateForm(instance=member)

    return render(request, "members/member_detail.html", {"form": form, 
                                                          "pk":pk, 
                                                          "writable": False, 
                                                          "editable": editable(request, member),
                                                          "managing_account_name": managing_member_name(member)})

def update_member(request, member=None, allow_change_account=False):
    # create a form instance and populate it with data from the request on existing member (or None):
    if not allow_change_account: # if we don't allow changing account, use a restricted form
        form = MemberUpdateNoAccountForm(instance=member)
    else:
        form = MemberUpdateForm(instance=member)
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        if not member:
            return HttpResponse("Error: No member to update")
        if form.is_valid(): form.save() 
        else: return HttpResponse(f"Error: Form is not valid {form.errors} >form instance {vars(form.instance)}\n{vars(form)}")
        # if no managing account, we use the logged user account
        member.refetch_from_db()
        if not member.managing_account:
            member.managing_account = User.objects.get(id=request.account.id)
            member.save()

        return HttpResponseRedirect(reverse("members:detail", kwargs={"pk":member.id}))
    # else:
        #     return HttpResponse(f"Error: Form is not valid {form.errors} >form instance {vars(form.instance)}")
        
    # if a GET (or any other method) we'll create a "blank" form prefilled by existing member (or empty if member = None)
    else:
        # if not allow_change_account:
        #     # form.fields['account'].widget.attrs['disabled'] = True
        #     form.fields['account'].disabled = True
        #     form.fields['account'].required = False
        return render(request, "members/member_detail.html", {"form": form, "pk":member.id if member else None,
                                                              "writable": editable(request, member), 
                                                              "editable": editable(request, member),
                                                              "managing_account_name": managing_member_name(member)})


@login_required
def change_member(request, pk=None):
    # if pk, get existing member
    member = get_object_or_404(Member, pk=pk) if pk else None
    # only first admin can change the account
    #print(f"super user? {request.user.is_superuser}")
    return update_member(request, member, allow_change_account=request.user.is_superuser)

@login_required
def profile(request):
    """change the profile of the logged user"""
    member = Member.objects.get(account__id=request.user.id)
    return update_member(request, member=member, allow_change_account=False)

# @login_required
# def profile(request):
#     if request.method == 'POST':
#         u_form = AccountUpdateForm(request.POST, instance=request.user)
#         p_form = ProfileUpdateForm(request.POST,
#                                    request.FILES,
#                                    instance=request.user.profile)
#         if u_form.is_valid() and p_form.is_valid():
#             u_form.save()
#             p_form.save()
#             messages.success(request, _('Your account has been updated!'))
#             return redirect('accounts:profile')

#     else:
#         u_form = AccountUpdateForm(instance=request.user)
#         p_form = ProfileUpdateForm(instance=request.user.profile)

#     context = {
#         'u_form': u_form,
#         'p_form': p_form
#     }

#     return render(request, 'accounts/profile.html', context)
