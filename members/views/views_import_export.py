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

from cousinsmatter.utils import assert_request_is_ajax

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
  warned_on_activate_users = False
  warnings = []
  errors = []
  row = None
  created_num = 0
  updated_num = 0
  rows_num = 0
  changed = False
  current_member = None

  def get_context_data(self, *args, **kwargs):
    optional_fields = {str(s) for s in ALL_FIELD_NAMES.values()} - {str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.values()}
    return super().get_context_data() | {
      'mandatory_fields': MANDATORY_MEMBER_FIELD_NAMES.values(),
      'optional_fields': optional_fields,
      'media_root': settings.MEDIA_ROOT,
      }

  def _create_member(self):
    """create new member based on current row content.
       returns created member and warnings if any
    """
    self.current_member = Member(is_active=False)
    self.changed = True
    # print(f"newly created member is active:{member.is_active}")
    for field in MEMBER_FIELD_NAMES:
      trfield = t(field)
      if trfield in self.row and self.row[trfield]:
        match field:
          case 'family':
            self._manage_family(self.row[trfield])
          case 'managed_by':
            self._manage_managed_by(self.row[trfield])
          case 'avatar':
            self._manage_avatar(self.row[trfield], self.row[t('username')])
          case _:
            if self.current_member.__dict__[field] != self.row[trfield]:
              setattr(self.current_member, field, self.row[trfield])

    self.current_member.is_active = self.activate_users and not self.current_member.is_dead
    # set manager to people who imported the file if imported users are not activated and not yet mmanaged
    if self.current_member.is_active:
      self.current_member.member_manager = None
    else:
      self.current_member.member_manager = self.current_member.member_manager or Member.objects.get(id=self.request.user.id) 
    self.current_member.password = generate_random_string(16)
    if self.changed:
      self.created_num += 1

  def _manage_avatar(self, avatar_file, username):
    avatar = os.path.join(settings.MEDIA_REL, settings.AVATARS_DIR, avatar_file)
    # avatar not changed
    if self.current_member.avatar and self.current_member.avatar.path == avatar:
      return

    # avatar image must already exist
    if not os.path.exists(avatar):
      self.warnings.append(_("Avatar not found: %(avatar)s for username %(username)s. Ignored...") %
                           {'avatar': avatar, 'username': username})
    else:
      try:
        with open(avatar, 'rb') as image_file:
          image = File(image_file)
          self.current_member.avatar.save(avatar_file, image)
          self.changed = True
      except Exception as e:
        self.warnings.append(_("Error saving avatar (%(warning)s): %(avatar)s for username %(username)s. Ignored...") %
                             {'warning': e, 'avatar': avatar, 'username': username})

  def _manage_family(self, family_name):
    if not self.current_member.family or self.current_member.family.name != family_name:
      self.current_member.family, _ = Family.objects.get_or_create(name=family_name)
      self.changed = True

  def _manage_managed_by(self, manager_username):
    # print(f"in manage_manage_by, member {self.current_member.username}, manager {manager_username}. "
    #       f"Member is {'active' if self.current_member.is_active else 'inactive'}. "
    #       f"Activate during Import is {self.activate_users}")
    if manager_username:
      new_member_manager = Member.objects.filter(username=manager_username).first()
      if self.activate_users and not self.warned_on_activate_users:
        self.warned_on_activate_users = True
        self.warnings.append(_("You requested to activate imported members. All managers will be ignored."))
      elif not new_member_manager:
        self.warnings.append(_("Manager %(manager)s not found for member %(member)s. Ignoring...") % {
          'manager': manager_username,
          'member': self.current_member.full_name})
      elif self.current_member.member_manager == new_member_manager:
        # no change
        pass
      elif self.current_member.is_active:
        self.warnings.append(_("Member %(member)s is active. Ignoring manager %(manager)s") % 
                             {'member': self.current_member.full_name, 'manager': manager_username})
      else:
        self.current_member.member_manager = new_member_manager
        self.changed = True
    else:  # no manager provided
      if not self.current_member.is_active:  # we need one
        if self.current_member.member_manager:
          # just ignore with a warning
          self.warnings.append(_("No manager provided for member %(member)s although inactive. "
                                 "Keeping existing one (%(manager)s)...") % {
                    'member': self.current_member.full_name, 'manager': self.current_member.member_manager.full_name})
        else:  # member is not active and has no manager, and none provided ==> error but continue
          self.errors.append(_("Inactive member %(member)s has no manager. Please provide one!") % {
            'member': self.current_member.full_name
            })
    # print(f"member {self.current_member.username} manager is "
    #       f"{self.current_member.member_manager.username if self.current_member.member_manager else 'None'}")

  def _update_member_field(self, field, value, username):
    match field:
      case 'username':
        pass
      case 'family':
        self._manage_family(value)
      case 'avatar':
        self._manage_avatar(value, username)
      case 'managed_by':
        self._manage_managed_by(value)
      case _:
        if self.current_member.__dict__[field] != value:
          setattr(self.current_member, field, value)
          self.changed = True

  def _update_member(self):
    "update an existing member based on current row content"
    # for all member fields but username
    # if new value for this field, then override existing one
    username = self.row[t('username')]
    for field in MEMBER_FIELD_NAMES:
      trfield = t(field)
      if trfield in self.row and self.row[trfield]:
        self._update_member_field(field, self.row[trfield], username)
    if self.activate_users and not self.current_member.is_active:
      self.current_member.member_manager = None
      self.current_member.is_active = True
      self.changed = True
    if self.changed:
      self.updated_num += 1

  def _update_address(self):
    address = {}
    for field in ADDRESS_FIELD_NAMES:
      trfield = t(field)
      if trfield in self.row:
        address[field] = self.row[trfield]
    # if len(address) == 5:   #we don't care if the address is incomplete
    if len(address) > 0:
      found = Address.objects.filter(**address).first()
      if found:
        if self.current_member.address != found:
          self.current_member.address = found
          self.changed = True
      else:
        address = Address.objects.create(**address)
        address.save()
        self.current_member.address = address
        self.changed = True

  def _import_csv(self, csv_file):
    csvf = io.TextIOWrapper(csv_file, encoding="utf-8", newline="")
    reader = csv.DictReader(csvf)
    check_fields(reader.fieldnames)
    random.seed()
    for self.row in reader:
      # reset all row variables
      self.warnings = []
      self.errors = []
      self.current_member = None
      self.changed = False
      # normalize username using slugify
      self.row[t('username')] = slugify(self.row[t('username')])
      # search for an existing member with this username
      self.current_member = Member.objects.filter(username=self.row[t('username')]).first()
      if self.current_member:  # found, update it
        self._update_member()
      else:  # not found, create it
        self._create_member()

      self._update_address()
      self.rows_num += 1

      if self.changed:
        self.current_member.save()

  def post(self, request, *args, **kwargs):
    self.request = request
    form = CSVImportMembersForm(request.POST, request.FILES)
    if form.is_valid():
      csv_file = request.FILES["csv_file"]
      self.activate_users = form.cleaned_data["activate_users"]

      try:
        self._import_csv(csv_file)
        messages.success(request,
                         _("CSV file uploaded: %(rows_num)i lines read, %(created_num)i members created "
                           "and %(updated_num)i updated.") %
                         {'rows_num': self.rows_num, 'created_num': self.created_num, 'updated_num': self.updated_num})
        for error in self.errors:
          messages.error(request, _("Error: %(error)s") % {'warning': error})
        for warning in self.warnings:
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
    assert_request_is_ajax(request)
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
    assert_request_is_ajax(request)
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
    assert_request_is_ajax(request)
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
