import logging
import csv
import random
import time
import os
import math
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
from django.contrib.auth.models import User
from ..models import Address, Member, Family
from ..forms import CSVImportMembersForm
from cousinsmatter.utils import redirect_to_referer
from django.conf import settings

from ..models import ALL_FIELD_NAMES, MANDATORY_FIELD_NAMES, ACCOUNT_FIELD_NAMES, MEMBER_FIELD_NAMES, ADDRESS_FIELD_NAMES

logger = logging.getLogger(__name__)


def generate_random_string(length):
    return ''.join(random.choice(string.printable) for _ in range(length))


def t(field): return ALL_FIELD_NAMES[field]


def check_fields(fieldnames):
  for fieldname in fieldnames:
    if fieldname not in ALL_FIELD_NAMES.values():
      raise ValidationError(_('Unknown column in CSV file: "%(fieldname)s". Valid fields are %(all_names)s') %
                            {'fieldname': fieldname, 'all_names': ', '.join([str(s) for s in ALL_FIELD_NAMES.values()])})
  for fieldname in MANDATORY_FIELD_NAMES.values():
    if fieldname not in fieldnames:
      raise ValidationError(_('Missing column in CSV file: "%(fieldname)s". Mandatory fields are %(all_names)s') %
                            {'fieldname': fieldname, 'all_names': ', '.join([str(s) for s in MANDATORY_FIELD_NAMES.values()])})

  return True


class CSVImportView(LoginRequiredMixin, generic.FormView):
  template_name = "members/import_members.html"
  form_class = CSVImportMembersForm
  success_url = reverse_lazy("members:members")

  def get_context_data(self, *args, **kwargs):
    optional_fields = {str(s) for s in ALL_FIELD_NAMES.values()} - {str(s) for s in MANDATORY_FIELD_NAMES.values()}
    return super().get_context_data() | {
      'mandatory_fields': MANDATORY_FIELD_NAMES.values(),
      'optional_fields': optional_fields,
      'media_root': settings.MEDIA_ROOT,
      }

  def _update_account(self, account, row, activate_users):
      """update account if needed"""
      changed = False
      # for all account fields but username
      # if new value for this field, then override existing one
      for field in ACCOUNT_FIELD_NAMES:
          if field == 'username':
              continue
          trfield = t(field)
          if row[trfield] and account.__dict__[field] != row[trfield]:
              setattr(account, field, row[trfield])
              changed = True
      if not account.is_active and activate_users:
          account.is_active = changed = True

      if changed:
          account.save()
      return changed

  def _create_account(self, row, activate_users):
      pwd = generate_random_string(16)
      return User.objects.create_user(row[t('username')], row[t('email')], pwd,
                                      first_name=row[t('first_name')],
                                      last_name=row[t('last_name')],
                                      is_active=activate_users)

  def _get_member(self, account, account_exists):
    if account_exists:  # then member also exists
        return Member.objects.get(account=account)
    else:
        # member will be created by user creation by using signals
        # so we have to wait for it to be created.
        timeout = 3  # wait max for 3s
        while timeout > 0:
            timeout -= 0.1
            time.sleep(0.1)
            member = Member.objects.filter(account=account).first()
            if member:
                return member
    raise TimeoutError()

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

  def _update_member(self, member, row, activate_users):
      changed = False
      error = None
      for field in MEMBER_FIELD_NAMES:
          trfield = t(field)
          if trfield in row and row[trfield] and member.__dict__[field] != row[trfield]:
              if field == 'family':
                  family = Family.objects.get_or_create(name=row[trfield], parent=None)
                  member.family = family
              elif field == 'avatar':
                  avatar = os.path.join(settings.MEDIA_ROOT, 'avatars', row[trfield])
                  # avatar image must already exist
                  if not os.path.exists(avatar):
                      error = _("Avatar not found: %(avatar)s for username %(username)s. Ignored...") % \
                              {'avatar': avatar, 'username': row[t('username')]}
                  else:
                      with open(avatar, 'rb') as image_file:
                          image = File(image_file)
                          member.avatar.save(avatar, image)
              else:
                  setattr(member, field, row[trfield])
              changed = True
      if member.account != member.managing_account and activate_users:
        member.managing_account = member.account
        changed = True

      return changed, error

  def _import_csv(self, csv_file, activate_users):
    nbMembers = 0
    nbLines = 0
    errors = []
    csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
    reader = csv.DictReader(csvf)
    check_fields(reader.fieldnames)
    random.seed()
    for row in reader:
        # search for an existing account with this username
        account_exists = False
        account = User.objects.filter(username=row[t('username')]).first()
        if account:  # found, use it
            account_exists = True
            self._update_account(account, row, activate_users)
        else:  # not found, create it
            account = self._create_account(row, activate_users)

        member = self._get_member(account, account_exists)
        changed_address = self._update_address(member, row)
        changed_member, error = self._update_member(member, row, activate_users)
        if error:
            errors.append(error)

        nbLines += 1

        if changed_address or changed_member:
            member.save()
            nbMembers += 1

    return (nbLines, nbMembers, errors)

  def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
    def size_in_mb(size):
      return math.floor(size*100/(1024*1024))/100

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
