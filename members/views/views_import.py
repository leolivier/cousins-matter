import logging
import csv
import random
import os
import io
import string
from django.core.files import File
from django.forms import ValidationError
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from ..models import Address, Member, Family
from ..forms import CSVImportMembersForm
from cousinsmatter.utils import redirect_to_referer
from django.conf import settings

from ..models import ALL_FIELD_NAMES, MANDATORY_MEMBER_FIELD_NAMES, MEMBER_FIELD_NAMES, ADDRESS_FIELD_NAMES

logger = logging.getLogger(__name__)


def generate_random_string(length):
  return ''.join(random.choice(string.printable) for _ in range(length))


def t(field): return ALL_FIELD_NAMES[field]


def check_fields(fieldnames):
  for fieldname in fieldnames:
    if fieldname not in ALL_FIELD_NAMES.values():
      raise ValidationError(_('Unknown column in CSV file: "%(fieldname)s". Valid fields are %(all_names)s') %
                            {'fieldname': fieldname, 'all_names': ', '.join([str(s) for s in ALL_FIELD_NAMES.values()])})
  for fieldname in MANDATORY_MEMBER_FIELD_NAMES.values():
    if fieldname not in fieldnames:
      raise ValidationError(_('Missing column in CSV file: "%(fieldname)s". Mandatory fields are %(all_names)s') %
                            {'fieldname': fieldname,
                             'all_names': ', '.join([str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.values()])})

  return True


class CSVImportView(LoginRequiredMixin, generic.FormView):
  template_name = "members/members/import_members.html"
  form_class = CSVImportMembersForm
  success_url = reverse_lazy("members:members")

  def get_context_data(self, *args, **kwargs):
    optional_fields = {str(s) for s in ALL_FIELD_NAMES.values()} - {str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.values()}
    return super().get_context_data() | {
      'mandatory_fields': MANDATORY_MEMBER_FIELD_NAMES.values(),
      'optional_fields': optional_fields,
      'media_root': settings.MEDIA_ROOT,
      }

  def _create_member(self, row, activate_users):
    """create new member based on row content.
       returns created member and errors if any
    """
    member = Member()
    error = None
    for field in MEMBER_FIELD_NAMES:
      trfield = t(field)
      if trfield in row and row[trfield] and member.__dict__[field] != row[trfield]:
        if field == 'family':
          self._manage_family(member, row[trfield])
        elif field == 'avatar':
          error = self._manage_avatar(member, row[trfield], row[t('username')])

        else:
          setattr(member, field, row[trfield])

    member.is_active = activate_users
    # set manager to people who imported the file if imported users are not activated
    member.managing_member = None if activate_users else Member.objects.get(id=self.request.user.id)
    member.password = generate_random_string(16)

    return member, error

  def _manage_avatar(self, member, avatar_file, username):
    avatar = os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, avatar_file)
    # avatar image must already exist
    if not os.path.exists(avatar):
        return _("Avatar not found: %(avatar)s for username %(username)s. Ignored...") % \
                {'avatar': avatar, 'username': username}
    else:
        with open(avatar, 'rb') as image_file:
            image = File(image_file)
            member.avatar.save(avatar, image)
        return None

  def _manage_family(self, member, family_name):
    member.family = Family.objects.get_or_create(name=family_name, parent=None)

  def _update_member(self, member, row, activate_users):
    "update an existing memebr based on row content"
    changed = False
    # for all member fields but username
    # if new value for this field, then override existing one
    error = None
    for field in MEMBER_FIELD_NAMES:
      if field == 'username':
        continue
      trfield = t(field)
      if trfield in row and row[trfield] and member.__dict__[field] != row[trfield]:
        if field == 'family':
          self._manage_family(member, row[trfield])
        elif field == 'avatar':
          error = self._manage_avatar(member, row[trfield], row[t('username')])
        else:
          setattr(member, field, row[trfield])
      changed = True

    if activate_users:
      if member.managing_member is not None:
        member.managing_member = None
        changed = True
      if not member.is_active:
        member.is_active = changed = True

    return changed, error

  def _update_address(self, member, row):
    changed = False
    address = {}
    for field in ADDRESS_FIELD_NAMES:
      trfield = t(field)
      if trfield in row:
        address[field] = row[trfield]
    # if len(address) == 5:   #we don't care if the address is incomplete
    if len(address) > 0:
      found = Address.objects.filter(**address).first()
      if found:
        if member.address != found:
          member.address = found
          changed = True
      else:
        address = Address.objects.create(**address)
        address.save()
        member.address = address
        changed = True
    return changed

  def _import_csv(self, csv_file, activate_users):
    nbMembers = 0
    nbLines = 0
    errors = []
    csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
    reader = csv.DictReader(csvf)
    check_fields(reader.fieldnames)
    random.seed()
    for row in reader:
      # search for an existing member with this username
      username = row[t('username')]
      member = Member.objects.filter(username=username).first()
      if member:  # found, use it
        changed_member, error = self._update_member(member, row, activate_users)
      else:  # not found, create it
        member, error = self._create_member(row, activate_users)
        changed_member = True

      changed_address = self._update_address(member, row)
      if error:
        errors.append(error)

      nbLines += 1

      if changed_address or changed_member:
        member.save()
        nbMembers += 1

    return (nbLines, nbMembers, errors)

  def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:

    self.request = request
    form = CSVImportMembersForm(request.POST, request.FILES)
    if form.is_valid():
      csv_file = request.FILES["csv_file"]
      activate_users = form.cleaned_data["activate_users"]

      try:
        nbLines, nbMembers, errors = self._import_csv(csv_file, activate_users)
        messages.success(request, _("CSV file uploaded: %(nbLines)i lines read, %(nbMembers)i members created or updated") %
                         {'nbLines': nbLines, 'nbMembers': nbMembers})
        for error in errors:
          messages.errors(request, _("Warning: %(error)s") % {'error': error})
      except ValidationError as ve:
        messages.error(request, ve.message)
        return redirect_to_referer(request)
      except Exception as e:
        messages.error(request, e.__str__())
        raise
    return super().post(request, *args, **kwargs)
