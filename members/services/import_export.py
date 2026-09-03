import csv
import io
import logging
import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _, get_language
from django_q.tasks import async_task, count_group, result_group
from django_q.brokers import get_broker

from ..models import (
  Member,
  ALL_FIELD_NAMES,
  MANDATORY_MEMBER_FIELD_NAMES,
  MEMBER_FIELD_NAMES,
  ADDRESS_FIELD_NAMES,
)
from members.tasks import ImportContext


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


def do_import_members_from_csv(csv_file, user_id, activate_users):
  default_manager = Member.objects.get(id=user_id)
  # task_group = request.POST.get("csrfmiddlewaretoken")  # not generated in test context
  task_group = uuid.uuid4().hex

  # carry the importer's tenant into the Q worker (no request/middleware there)
  import_context = ImportContext(
    default_manager=default_manager,
    activate_users=activate_users,
    group=task_group,
    lang=get_language(),
    tenant_id=default_manager.tenant_id,
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


def get_import_progress(id):
  import_data = ImportContext.get(id)
  if not import_data:  # removed from the list when completed
    raise ObjectDoesNotExist(_("Import not found"))
  import_data.current_count = count_group(id)

  # get already finished tasks
  results = result_group(id, failures=True, count=import_data.current_count, cached=False)
  # print error messages first then successful import
  if results:
    for row_data in results:
      if row_data.is_created():
        import_data.created_num += 1
      elif row_data.is_updated():
        import_data.updated_num += 1
      import_data.errors.append(row_data.errors)
      import_data.warnings.append(row_data.warnings)
      import_data.users.append(row_data.current_member.username)

  if import_data.current_count == import_data.rows_num:  # reached the end
    import_data.unregister()
    logger.debug(f"cleaned {import_data}")
  return import_data


def do_export_members_to_csv(stream, city=None, family=None, name=None):
  members = Member.objects.all()
  if city:
    members = members.filter(address__city=city)
  if family:
    members = members.filter(family__name=family)
  if name:
    members = members.filter(last_name=name)

  # print([(m.last_name, m.address.city if m.address else '', m.family.name if m.family else '') for m in members])
  # print(members.query)

  writer = csv.writer(stream)

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
