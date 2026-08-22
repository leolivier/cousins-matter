import logging
from django.views import generic
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from core.htmx import htmx_refresh
from core.decorators import require_htmx

from ..models import Family
from ..forms import FamilyUpdateForm

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


class ModalFamilyUpsertMixin(generic.View):
  model = Family
  template_name = "members/family/family_form.html"
  form_class = FamilyUpdateForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title
    return context

  @require_htmx()
  def process_form(self, request, form):
    if form.is_valid():
      family = form.save()
      # TODO: very inefficient! refactor to add a search field
      families = Family.objects.all()
      child_family_id = request.GET.get("current_family_id", "")
      if child_family_id:
        child_family = get_object_or_404(Family, pk=child_family_id)
        child_family.parent = family
        child_family.save(update_fields=["parent"])
      return render(request, "members/family/family_form.html#set_family", {"selected_family": family, "families": families})
    else:
      messages.error(request, form.errors)
      return htmx_refresh()


class ModalFamilyCreateView(ModalFamilyUpsertMixin, generic.CreateView):
  title = _("New Family")

  def post(self, request, *args, **kwargs):
    form = FamilyUpdateForm(request.POST)
    return self.process_form(request, form)


class ModalFamilyUpdateView(ModalFamilyUpsertMixin, generic.UpdateView):
  title = _("Change Family")

  def post(self, request, *args, **kwargs):
    family = get_object_or_404(Family, pk=kwargs["pk"])
    form = FamilyUpdateForm(request.POST, instance=family)
    return self.process_form(request, form)
