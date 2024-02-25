from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Member, Address, Family
from .forms import MemberForm

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

@login_required
def get_member(request, pk=None):
    # if pk, get existing member
    member = get_object_or_404(Member, pk=pk) if pk else None
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request on existing member (or None):
        form = MemberForm(request.POST, instance = member)
        # save the form (it checks whether form is valid):
        form.save()
        return HttpResponseRedirect(reverse("members:members"))

    # if a GET (or any other method) we'll create a "blank" form prefilled by existing member (or None)
    else:
        form = MemberForm(instance=member)

    return render(request, "members/member_detail.html", {"form": form, "pk":pk})