import logging
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from ..models import Family
from ..forms import FamilyUpdateForm
from cousinsmatter.utils import assert_request_is_ajax

logger = logging.getLogger(__name__)


class FamilyDetailView(LoginRequiredMixin, generic.DetailView):
    model = Family
    template_name = "members/family/family_detail.html"


class FamilyCreateView(LoginRequiredMixin, generic.CreateView):
    model = Family
    template_name = "members/family/family_form.html"
    fields = "__all__"


class FamilyUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Family
    template_name = "members/family/family_form.html"
    fields = "__all__"


def _json_family_response(family):
  return JsonResponse({"family_id": family.id, "family_name": str(family),
                       "parent_family_id": family.parent.id if family.parent else ''},
                      status=200)


class ModalFamilyUpsertViewMixin(LoginRequiredMixin):
  model = Family
  template_name = "members/family/family_form.html"
  fields = "__all__"

  def process_form(self, request, form):
    assert_request_is_ajax(request)
    if form.is_valid():
      family = form.save()
      return _json_family_response(family)
    else:
      errors = form.errors.as_json()
      return JsonResponse({"errors": errors}, status=400)


class ModalFamilyCreateView(ModalFamilyUpsertViewMixin, generic.CreateView):
  def post(self, request, *args, **kwargs):
    # create a form instance from the request and save it
    form = FamilyUpdateForm(request.POST)
    return self.process_form(request, form)


class ModalFamilyUpdateView(ModalFamilyUpsertViewMixin, generic.UpdateView):
  def post(self, request, *args, **kwargs):
    family = get_object_or_404(Family, pk=kwargs['pk'])
    # create a form instance and populate it with data from the request on existing member (or None):
    form = FamilyUpdateForm(request.POST, instance=family)
    return self.process_form(request, form)


@login_required
def get_family(request, pk):
  assert_request_is_ajax(request)
  family = get_object_or_404(Family, pk=pk)
  return _json_family_response(family)
