import logging
import csv
import random
import os
import io
import string

from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from cousinsmatter.utils import is_ajax

from ..models import Address, Member, Family
from ..forms import CSVImportMembersForm
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
       returns created member and warnings if any
    """
    member = Member()
    warnings = []
    for field in MEMBER_FIELD_NAMES:
      trfield = t(field)
      if trfield in row and row[trfield]:
        if field == 'family':
          self._manage_family(member, row[trfield])
        elif field == 'avatar':
          warning = self._manage_avatar(member, row[trfield], row[t('username')])
          if warning:
            warnings.append(warning)
        elif member.__dict__[field] != row[trfield]:
          setattr(member, field, row[trfield])

    member.is_active = activate_users and not member.is_dead
    # set manager to people who imported the file if imported users are not activated
    member.managing_member = None if member.is_active else Member.objects.get(id=self.request.user.id)
    member.password = generate_random_string(16)

    return member, warnings

  def _manage_avatar(self, member, avatar_file, username):
    avatar = os.path.join(settings.MEDIA_REL, settings.AVATARS_DIR, avatar_file)
    # avatar not changed
    if member.avatar and member.avatar.path == avatar:
      return (None, False)

    # avatar image must already exist
    if not os.path.exists(avatar):
      return (_("Avatar not found: %(avatar)s for username %(username)s. Ignored...") %
              {'avatar': avatar, 'username': username}, False)
    else:
      try:
        with open(avatar, 'rb') as image_file:
          image = File(image_file)
          member.avatar.save(avatar_file, image)
          return (None, False)
      except Exception as e:
        return (_("Error saving avatar (%(warning)s): %(avatar)s for username %(username)s. Ignored...") %
                {'warning': e, 'avatar': avatar, 'username': username}, False)

  def _manage_family(self, member, family_name):
    if member.family and member.family.name == family_name:
      return False
    member.family, created = Family.objects.get_or_create(name=family_name)
    return True

  def _update_member_field(self, member, field, value, username):
      changed = False
      warnings = []

      match field:
        case 'username':
          pass
        case 'family':
          changed = self._manage_family(member, value)
        case 'avatar':
          warning, modified = self._manage_avatar(member, value, username)
          changed = changed or modified
          if warning:
            warnings.append(warning)
        case _:
          if member.__dict__[field] != value:
            setattr(member, field, value)
            changed = True

      return (changed, warnings)

  def _update_member(self, member, row, activate_users):
    "update an existing member based on row content"
    changed = False
    # for all member fields but username
    # if new value for this field, then override existing one
    warnings = []
    username = row[t('username')]
    for field in MEMBER_FIELD_NAMES:
      trfield = t(field)
      if trfield in row and row[trfield]:
        modified, new_warnings = self._update_member_field(member, field, row[trfield], username)
        changed = changed or modified
        warnings.extend(new_warnings)
    if activate_users and not member.is_dead:
      if member.managing_member is not None:
        member.managing_member = None
        changed = True
      if not member.is_active:
        member.is_active = changed = True

    return changed, warnings

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
    all_warnings = []
    csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
    reader = csv.DictReader(csvf)
    check_fields(reader.fieldnames)
    random.seed()
    for row in reader:
      # normalize username using slugify
      username = slugify(row[t('username')])
      row[t('username')] = username
      # search for an existing member with this username
      member = Member.objects.filter(username=username).first()
      if member:  # found, use it
        changed_member, new_warnings = self._update_member(member, row, activate_users)
      else:  # not found, create it
        member, new_warnings = self._create_member(row, activate_users)
        changed_member = True

      changed_address = self._update_address(member, row)
      all_warnings.extend(new_warnings)

      nbLines += 1

      if changed_address or changed_member:
        member.save()
        nbMembers += 1

    return (nbLines, nbMembers, all_warnings)

  def post(self, request, *args, **kwargs):
    self.request = request
    form = CSVImportMembersForm(request.POST, request.FILES)
    if form.is_valid():
      csv_file = request.FILES["csv_file"]
      activate_users = form.cleaned_data["activate_users"]

      try:
        nbLines, nbMembers, warnings = self._import_csv(csv_file, activate_users)
        messages.success(request, _("CSV file uploaded: %(nbLines)i lines read, %(nbMembers)i members created or updated") %
                         {'nbLines': nbLines, 'nbMembers': nbMembers})
        for warning in warnings:
          messages.warning(request, _("Warning: %(warning)s") % {'warning': warning})
      except ValidationError as ve:
        messages.error(request, ve.message)
        return render(request, self.template_name, {'form': form})
      except Exception as e:
        messages.error(request, e.__str__())
        raise
    return super().post(request, *args, **kwargs)


@login_required
def select_name(request):
    if not is_ajax(request):
      raise ValidationError("Forbidden non ajax request")

    query = request.GET.get('q', '')
    # List of matching names, case insensitive, limited to 12 results
    names = Member.objects.filter(last_name__icontains=query) \
                          .values_list('last_name', flat=True) \
                          .distinct() \
                          .order_by('last_name')[:12]
    t_names = set(name.title() for name in names)
    data = [{'id': name, 'text': name} for name in t_names]
    return JsonResponse({'results': data})


@login_required
def select_family(request):
    if not is_ajax(request):
      raise ValidationError("Forbidden non ajax request")

    query = request.GET.get('q', '')
    # List of matching familynames, case insensitive, limited to 12 results
    families = Family.objects.filter(name__icontains=query) \
                             .values_list('name', flat=True) \
                             .distinct() \
                             .order_by('name')[:12]
    t_families = set(family.title() for family in families)
    data = [{'id': family, 'text': family} for family in t_families]
    return JsonResponse({'results': data})


@login_required
def select_city(request):
    if not is_ajax(request):
      raise ValidationError("Forbidden non ajax request")

    query = request.GET.get('q', '')
    # List of matching city names, case insensitive, limited to 12 results
    cities = Address.objects.filter(city__icontains=query) \
                            .values_list('city', flat=True) \
                            .distinct() \
                            .order_by('city')[:12]
    t_cities = set(city.title() for city in cities)
    data = [{'id': city, 'text': city} for city in t_cities]

    return JsonResponse({'results': data})


@login_required
def select_members_to_export(request):
  return render(request, 'members/members/export_members.html')


@login_required
def export_members_to_csv(request):
  if request.method != 'POST':
    raise ValidationError(_('Method not allowed'))

  city = request.POST.get('city-id')
  family = request.POST.get('family-id')
  name = request.POST.get('name-id')
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
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="members.csv"'

  writer = csv.writer(response)

  # Write CSV header
  writer.writerow(ALL_FIELD_NAMES.values())

  # Retrieve member data
  members = members.select_related('address').select_related('family').order_by('username')

  # Write member data to CSV file
  for member in members:
    row = []
    for field in MEMBER_FIELD_NAMES.keys():
      if field == 'family':
        row.append(member.family.name if member.family else '')
      else:
        row.append(getattr(member, field, ''))
    for field in ADDRESS_FIELD_NAMES.keys():
      row.append(getattr(member.address, field, '') if member.address else '')
    writer.writerow(row)

  return response
