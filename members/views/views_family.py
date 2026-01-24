import logging
from django.views import generic
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..models import Family
from ..forms import FamilyUpdateForm
from cm_main.utils import assert_request_is_ajax

logger = logging.getLogger(__name__)


class FamilyDetailView(generic.DetailView):
  model = Family
  template_name = "members/family/family_detail.html"


class FamilyCreateView(generic.CreateView):
  model = Family
  template_name = "members/family/family_form.html"
  fields = "__all__"


class FamilyUpdateView(generic.UpdateView):
  model = Family
  template_name = "members/family/family_form.html"
  fields = "__all__"


def _json_family_response(family):
  return JsonResponse(
    {
      "family_id": family.id,
      "family_name": str(family),
      "parent_family_id": family.parent.id if family.parent else "",
    },
    status=200,
  )


class ModalFamilyUpsertMixin(generic.View):
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


class ModalFamilyCreateView(ModalFamilyUpsertMixin, generic.CreateView):
  def post(self, request, *args, **kwargs):
    # create a form instance from the request and save it
    form = FamilyUpdateForm(request.POST)
    return self.process_form(request, form)


class ModalFamilyUpdateView(ModalFamilyUpsertMixin, generic.UpdateView):
  def post(self, request, *args, **kwargs):
    family = get_object_or_404(Family, pk=kwargs["pk"])
    # create a form instance and populate it with data from the request on existing member (or None):
    form = FamilyUpdateForm(request.POST, instance=family)
    return self.process_form(request, form)


def get_family(request, pk):
  assert_request_is_ajax(request)
  family = get_object_or_404(Family, pk=pk)
  return _json_family_response(family)
