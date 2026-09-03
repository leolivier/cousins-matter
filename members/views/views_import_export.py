import logging

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.utils.translation import gettext_lazy as _

from core.utils import assert_request_is_ajax

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


def select_name(request):
  assert_request_is_ajax(request)
  query = request.GET.get("q", "")
  # List of matching names, case insensitive, limited to 12 results
  names = (
    Member.objects.filter(last_name__icontains=query).values_list("last_name", flat=True).distinct().order_by("last_name")[:12]
  )
  t_names = set(name.title() for name in names)
  data = [{"id": name, "text": name} for name in t_names]
  return JsonResponse({"results": data})


def select_family(request):
  assert_request_is_ajax(request)
  query = request.GET.get("q", "")
  # List of matching familynames, case insensitive, limited to 12 results
  families = Family.objects.filter(name__icontains=query).values_list("name", flat=True).distinct().order_by("name")[:12]
  t_families = set(family.title() for family in families)
  data = [{"id": family, "text": family} for family in t_families]
  return JsonResponse({"results": data})


def select_city(request):
  assert_request_is_ajax(request)
  query = request.GET.get("q", "")
  # List of matching city names, case insensitive, limited to 12 results
  cities = Address.objects.filter(city__icontains=query).values_list("city", flat=True).distinct().order_by("city")[:12]
  t_cities = set(city.title() for city in cities)
  data = [{"id": city, "text": city} for city in t_cities]

  return JsonResponse({"results": data})


def select_members_to_export(request):
  return render(request, "members/members/export_members.html")


def export_members_to_csv(request):
  if request.method != "POST":
    raise ValidationError(_("Method not allowed"))

  city = request.POST.get("city-id")
  family = request.POST.get("family-id")
  name = request.POST.get("name-id")
  # print('city: ', city, ' family: ', family, ' name: ', name)

  # Create an HTTP response with the CSV content type
  response = HttpResponse(content_type="text/csv")
  response["Content-Disposition"] = 'attachment; filename="members.csv"'

  do_export_members_to_csv(response, city=city, family=family, name=name)

  return response
