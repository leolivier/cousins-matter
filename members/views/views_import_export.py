import logging
import csv
import io
import uuid
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _, get_language
from django_q.tasks import async_task, count_group, result_group
from django_q.brokers import get_broker

from cm_main.utils import assert_request_is_ajax
from members.tasks import ImportContext

from ..models import Address, Member, Family
from ..forms import CSVImportMembersForm
from django.conf import settings

from ..models import ALL_FIELD_NAMES, MANDATORY_MEMBER_FIELD_NAMES, MEMBER_FIELD_NAMES, ADDRESS_FIELD_NAMES

logger = logging.getLogger(__name__)


def t(field: str) -> str:
  return ALL_FIELD_NAMES[field]


def check_fields(fieldnames: list[str]):
  for fieldname in fieldnames:
    if fieldname not in ALL_FIELD_NAMES.values():
      raise ValidationError(
        _('Unknown column in CSV file: "%(fieldname)s". Valid fields are %(all_names)s')
        % {"fieldname": fieldname, "all_names": ", ".join([str(s) for s in ALL_FIELD_NAMES.values()])}
      )
  for fieldname in MANDATORY_MEMBER_FIELD_NAMES.values():
    if fieldname not in fieldnames:
      raise ValidationError(
        _('Missing column in CSV file: "%(fieldname)s". Mandatory fields are %(all_names)s')
        % {"fieldname": fieldname, "all_names": ", ".join([str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.values()])}
      )

  return True


def import_csv(csv_file, task_group, user_id, activate_users):
  default_manager = Member.objects.get(id=user_id)
  import_context = ImportContext(
    default_manager=default_manager, activate_users=activate_users, group=task_group, lang=get_language()
  )
  import_context.register()
  csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
  reader = csv.DictReader(csvf)
  check_fields(reader.fieldnames)
  broker = get_broker()
  for row in reader:
    logger.debug(f"create task #{import_context.rows_num + 1} for importing row: {row}")
    async_task("members.tasks.import_row", import_context, row, broker=broker, group=task_group)
    import_context.rows_num += 1
  logger.info("importing %d rows", import_context.rows_num)

  return import_context


class CSVImportView(LoginRequiredMixin, generic.FormView):
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
        # task_group = request.POST.get("csrfmiddlewaretoken")  # not generated in test context
        task_group = uuid.uuid4().hex

        import_data = import_csv(csv_file, task_group, request.user.id, activate_users)

        hx_get_url = reverse("members:import_progress", args=(task_group,))
        logger.debug(f"rendering first progress-bar url: {hx_get_url} task group: {task_group}")
        return render(
          request,
          "cm_main/common/progress-bar.html",
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


@login_required
def import_progress(request, id):
  import_data = ImportContext.get(id)
  if not import_data:  # removed from the list when completed
    raise Http404(_("Import not found"))
  value = count_group(id)
  max = import_data.rows_num

  # get already finished tasks
  results = result_group(id, failures=True, count=value, cached=False)
  # print error messages first then successful import
  errors = []
  warnings = []
  users = []
  if results:
    for row_data in results:
      if row_data.is_created():
        import_data.created_num += 1
      elif row_data.is_updated():
        import_data.updated_num += 1
      errors.append(row_data.errors)
      warnings.append(row_data.warnings)
      users.append(row_data.current_member.username)
  context = {
    "hx_get": request.get_full_path(),
    "frequency": "1s",
    "value": value,
    "max": max,
    "text": str(int(value * 100 / max)) + "%",
    "processed_objects": users,
    "errors": errors,
    "warnings": warnings,
  }
  if value == max:  # reached the end
    context["back_url"] = reverse("members:members")
    context["back_text"] = _("Back to members list")
    context["success"] = _(
      "CSV file uploaded: %(rows_num)i lines read, %(created_num)i members created and %(updated_num)i updated."
    ) % {"rows_num": import_data.rows_num, "created_num": import_data.created_num, "updated_num": import_data.updated_num}
    # remove zimport from the cache
    import_data.unregister()
    logger.debug(f"cleaned {import_data}")
  logger.debug(
    f"upload progress bar value: {value}, max: {max}, processed objects: {users}, errors: {errors}, warnings: {warnings}"
  )
  return render(request, "cm_main/common/progress-bar.html", context)


@login_required
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


@login_required
def select_family(request):
  assert_request_is_ajax(request)
  query = request.GET.get("q", "")
  # List of matching familynames, case insensitive, limited to 12 results
  families = Family.objects.filter(name__icontains=query).values_list("name", flat=True).distinct().order_by("name")[:12]
  t_families = set(family.title() for family in families)
  data = [{"id": family, "text": family} for family in t_families]
  return JsonResponse({"results": data})


@login_required
def select_city(request):
  assert_request_is_ajax(request)
  query = request.GET.get("q", "")
  # List of matching city names, case insensitive, limited to 12 results
  cities = Address.objects.filter(city__icontains=query).values_list("city", flat=True).distinct().order_by("city")[:12]
  t_cities = set(city.title() for city in cities)
  data = [{"id": city, "text": city} for city in t_cities]

  return JsonResponse({"results": data})


@login_required
def select_members_to_export(request):
  return render(request, "members/members/export_members.html")


@login_required
def export_members_to_csv(request):
  if request.method != "POST":
    raise ValidationError(_("Method not allowed"))

  city = request.POST.get("city-id")
  family = request.POST.get("family-id")
  name = request.POST.get("name-id")
  # print('city: ', city, ' family: ', family, ' name: ', name)

  members = Member.objects.all()
  if city:
    members = members.filter(address__city=city)
  if family:
    members = members.filter(family__name=family)
  if name:
    members = members.filter(last_name=name)

  # print([(m.last_name, m.address.city if m.address else '', m.family.name if m.family else '') for m in members])
  # print(members.query)
  # Create an HTTP response with the CSV content type
  response = HttpResponse(content_type="text/csv")
  response["Content-Disposition"] = 'attachment; filename="members.csv"'

  writer = csv.writer(response)

  # Write CSV header
  writer.writerow(ALL_FIELD_NAMES.values())

  # Retrieve member data
  members = members.select_related("address").select_related("family").select_related("member_manager").order_by("username")

  # Write member data to CSV file
  for member in members:
    row = []
    for field in MEMBER_FIELD_NAMES.keys():
      if field == "family":
        row.append(member.family.name if member.family else "")
      elif field == "managed_by":
        row.append(member.member_manager.username if member.member_manager else "")
      else:
        row.append(getattr(member, field, ""))
    for field in ADDRESS_FIELD_NAMES.keys():
      row.append(getattr(member.address, field, "") if member.address else "")
    writer.writerow(row)

  return response
