import logging

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.utils.translation import gettext_lazy as _

from core.decorators import require_htmx

from ..models import (
  Address,
  Member,
  Family,
  ALL_FIELD_NAMES,
  MANDATORY_MEMBER_FIELD_NAMES,
)
from ..forms import CSVImportMembersForm
from ..services.import_export import (
  do_import_members_from_csv,
  do_export_members_to_csv,
  get_import_progress,
)

logger = logging.getLogger(__name__)


class CSVImportView(generic.FormView):
  template_name = "members/members/import_members.html"
  form_class = CSVImportMembersForm
  success_url = reverse_lazy("members:members")

  def get_context_data(self, *args, **kwargs):
    optional_fields = {str(s) for s in ALL_FIELD_NAMES.values()} - {str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.values()}
    return super().get_context_data() | {
      "mandatory_fields": MANDATORY_MEMBER_FIELD_NAMES.values(),
      "optional_fields": optional_fields,
      "media_root": settings.MEDIA_ROOT,
    }

  def post(self, request, *args, **kwargs):
    self.request = request
    form = CSVImportMembersForm(request.POST, request.FILES)
    if form.is_valid():
      try:
        csv_file = request.FILES["csv_file"]
        activate_users = form.cleaned_data["activate_users"]

        import_data = do_import_members_from_csv(csv_file, request.user.id, activate_users)

        hx_get_url = reverse("members:import_progress", args=(import_data.task_group,))
        logger.debug(f"rendering first progress-bar url: {hx_get_url} task group: {import_data.task_group}")
        return render(
          request,
          "core/common/progress-bar.html",
          {"hx_get": hx_get_url, "frequency": "1s", "value": 0, "max": import_data.rows_num, "text": "0%"},
        )
      except ValidationError as ve:
        logger.error(ve.message)
        messages.error(request, ve.message)
        return redirect(reverse("members:csv_import"))
      except Exception as e:
        logger.error(e.__str__())
        messages.error(request, e.__str__())
        return redirect(reverse("members:csv_import"))
    return redirect(reverse("members:csv_import"))


def import_progress(request, id):
  try:
    import_data = get_import_progress(id)
  except ObjectDoesNotExist:
    raise Http404(_("Import not found"))

  import_data.rows_num = import_data.rows_num

  context = {
    "hx_get": request.get_full_path(),
    "frequency": "1s",
    "value": import_data.current_count,
    "max": import_data.rows_num,
    "text": str(int(import_data.current_count * 100 / import_data.rows_num)) + "%",
    "processed_objects": import_data.users,
    "errors": import_data.errors,
    "warnings": import_data.warnings,
  }
  if import_data.current_count == import_data.rows_num:  # reached the end
    context["back_url"] = reverse("members:members")
    context["back_text"] = _("Back to members list")
    context["success"] = _(
      "CSV file uploaded: %(rows_num)i lines read, %(created_num)i members created and %(updated_num)i updated."
    ) % {"rows_num": import_data.rows_num, "created_num": import_data.created_num, "updated_num": import_data.updated_num}
  logger.debug(
    f"upload progress bar value: {import_data.current_count}, "
    + f"max: {import_data.rows_num}, "
    + f"processed objects: {import_data.users}, "
    + f"errors: {import_data.errors}, "
    + f"warnings: {import_data.warnings}"
  )
  return render(request, "core/common/progress-bar.html", context)


@require_htmx()
def select_by_model_field(request, model, field) -> HttpResponse:
  query = request.GET.get("q", "")
  # print("query", query, "model", model, "field", field)
  # List of matching names, case insensitive, limited to 12 results
  items: set[str] = set(
    model.objects.filter(**{f"{field}__icontains": query}).values_list(field, flat=True).distinct().order_by(field)[:12]
  )
  data: list[dict[str, str]] = [{"id": item, "text": item} for item in items]
  return render(request, template_name="core/common/htmx_search.html#select_dropdown_results", context={"results": data})


def select_name(request) -> HttpResponse:
  return select_by_model_field(request, Member, "last_name")


def select_family(request) -> HttpResponse:
  return select_by_model_field(request, Family, "name")


def select_city(request) -> HttpResponse:
  return select_by_model_field(request, Address, "city")


def select_members_to_export(request) -> HttpResponse:
  return render(
    request,
    template_name="members/members/export_members.html",
    context={"fields": ["family", "city", "name"], "initial_count": Member.objects.count()},
  )


def count_selected(request) -> HttpResponse:
  family = request.GET.get("family-select-id")
  city = request.GET.get("city-select-id")
  name = request.GET.get("name-select-id")

  qs = Member.objects.all().only("id")
  if family:
    qs = qs.filter(family__name=family)
  if city:
    qs = qs.filter(address__city=city)
  if name:
    qs = qs.filter(last_name=name)

  # print("qs: ", qs.query, "count: ", qs.count())

  return HttpResponse(content=str(qs.count()))


def export_members_to_csv(request) -> HttpResponse:
  if request.method != "POST":
    raise ValidationError(_("Method not allowed"))

  city = request.POST.get("city-select-id")
  family = request.POST.get("family-select-id")
  name = request.POST.get("name-select-id")
  print("city: ", city, " family: ", family, " name: ", name)

  # Create an HTTP response with the CSV content type
  response = HttpResponse(content_type="text/csv")
  response["Content-Disposition"] = 'attachment; filename="members.csv"'

  do_export_members_to_csv(response, city=city, family=family, name=name)

  return response
