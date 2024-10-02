import csv
from datetime import date
import io
import os
import shutil

from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import translation
# from django.utils.translation import gettext as _

from ..models import ALL_FIELD_NAMES, MANDATORY_MEMBER_FIELD_NAMES, Member, Address
from .tests_member_base import MemberTestCase
from ..views.views_import_export import CSVImportView


def get_test_file(filename):
  return os.path.join(os.path.dirname(__file__), 'resources', filename)


class TestImportMixin():
  def do_upload_file(self, file, lang, activate_users=True):
    url = reverse('members:csv_import')
    csv_file = get_test_file(file)
    # force language to make sure the CSV fields are ok
    with translation.override(lang):
      response = self.client.post(url,
                                  {'csv_file': SimpleUploadedFile(file,
                                                                  open(csv_file, 'rb').read(),
                                                                  content_type='text/csv'),
                                    'activate_users': activate_users
                                   }, follow=True, HTTP_ACCEPT_LANGUAGE=lang)
    # print(response.content)
    return response

  def do_test_import(self, file, lang, expected_num, activate_users=True, member_prefix='member'):
    prev_num = Member.objects.count()
    response = self.do_upload_file(file, lang)
    self.assertEqual(response.status_code, 200)
    # Check that expected_num members were imported
    self.assertEqual(Member.objects.count(), prev_num+expected_num)
    # Check that specific members were created
    self.assertTrue(Member.objects.filter(first_name='John', last_name='Doe').exists())
    self.assertTrue(Member.objects.filter(email='member2@test.com').exists())
    self.assertTrue(Member.objects.filter(birthdate=date(2000, 1, 3)).exists())
    self.assertTrue(Address.objects.filter(city='Blackpool').exists())
    self.assertTrue(Member.objects.filter(address__city='Blackpool').exists())
    for i in range(4):
      name = member_prefix + str(i+1)
      # print("name=", name)
      m = Member.objects.get(username=name)
      if activate_users:
        self.assertEqual(m.is_active, activate_users)
        self.assertIsNone(m.managing_member)
      else:  # managing_member is None if and only if active
        self.assertEqual(m.managing_member is None, m.is_active)


class TestMemberImport(TestImportMixin, MemberTestCase):

  def setUp(self):
    super().setUp()
    # create several avatars based on test_avatar_jpg
    for i in range(5):
      avatar = os.path.join(settings.MEDIA_ROOT, 'avatars', 'test_avatar_%d.jpg' % i)
      if not os.path.exists(avatar):
        avatar_from = os.path.join(os.path.dirname(__file__), 'resources', self.base_avatar)
        if not os.path.exists(avatar_from):
          raise Exception("Test avatar file not found in resources")
        shutil.copyfile(avatar_from, avatar)

  def test_get_import(self):
    response = self.client.get(reverse('members:csv_import'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/members/import_members.html')
    self.assertIs(response.resolver_match.func.view_class, CSVImportView)

  def test_import_en(self):
    """test the import in english (create and update)"""
    # more or less the same as 1rst line of import file with differences on first_name, birthdate and phone
    data = {'username': "member1", 'email': "member1@test.com", 'password': self.password,
            'first_name': "Johnny", 'last_name': "Doe", 'birthdate': date(2001, 1, 1), 'phone': "+45 01 02 30"}
    member1 = self.create_member(data)
    self.do_test_import('import_members.csv', 'en-us', 3)  # expected 3 and not 4 because we just created one above
    member1.refresh_from_db()
    # check the changes have been taken from the import file
    self.assertEqual(member1.first_name, "John")
    self.assertEqual(member1.birthdate, date(2000, 1, 1))
    self.assertEqual(member1.phone, "+45 01 02 03")

  def test_import_fr(self):
    self.do_test_import('import_members-fr.csv', 'fr', 4, member_prefix='member-fr')

  def test_wrong_field(self):
    response = self.do_upload_file('import_members-wrong-field.csv', 'en-us')
    self.assertEqual(response.status_code, 200)
    # force language to make sure the CSV fields are ok
    with translation.override('en-us'):
      self.assertContainsMessage(
        response, "error",
        'Unknown column in CSV file: "%(fieldname)s". Valid fields are %(all_names)s' % {
          'fieldname': "citi",
          'all_names': ', '.join([str(s) for s in ALL_FIELD_NAMES.values()])
        })

  def test_missing_field(self):
    response = self.do_upload_file('import_members-missing-field.csv', 'en-us')
    self.assertEqual(response.status_code, 200)
    self.assertContainsMessage(response, "error",
                               'Missing column in CSV file: \"%(fieldname)s\". Mandatory fields are %(all_names)s' % {
                                   'fieldname': "first_name",
                                   'all_names': ", ".join([str(s) for s in MANDATORY_MEMBER_FIELD_NAMES.keys()])
                               })


class CSVExportViewTests(TestImportMixin, MemberTestCase):

  def matches_filter(self, row, filter):
    """returns True if row is filtered according to filter"""

    if filter:
      filter = {k: v for k, v in filter.items() if v != ''}  # remove empty values

    if not filter:  # can be None or {}
      return False

    map = {
      'city-id': ALL_FIELD_NAMES['city'],
      'family-id': ALL_FIELD_NAMES['family'],
      'name-id': ALL_FIELD_NAMES['last_name']
    }

    # print("check filters for row=%s filter=%s" % (row, filter))
    for filter_key, filter_val in filter.items():
      # print("checking filter %s=%s" % (filter_key, filter_val))
      field = map[filter_key]
      row_val = row.get(field)
      if filter_val != row_val:
        # print("filter_val=%s != row_val=%s => not matching" % (filter_val, row_val))
        return False
    # print('All filters match')
    return True

  def check_CSVs_are_equivalent(self, exp_csv, rsp_csv, filter=None):
    """
    Utility function to check the equivalence of two CSVs in the context of this test class.
    exp_csv and rsp_csv must be csv.DictReader objects.
    All lines of exp_csv should be in rsp_csv plus the lines about self.member and self.superuser
    """
    # check that rsp_csv columns (received columns) contains all defined columns
    for column in [str(s) for s in ALL_FIELD_NAMES.values()]:
      self.assertTrue(column in rsp_csv.fieldnames, msg="Column %s not in received CSV" % column)

    username_key = ALL_FIELD_NAMES['username']  # get the key for username
    # transform both csvs into dict of rows indexed by username and a list of usernames
    rsp_rows = {row[username_key]: row for row in list(rsp_csv)}
    rsp_usernames = rsp_rows.keys()

    exp_rows = {row[username_key]: row for row in list(exp_csv)}
    exp_usernames = exp_rows.keys()

    # check that rsp_csv does not contain lines that should have been filtered
    if filter:
      for rsp_row in rsp_rows.values():
        self.assertTrue(self.matches_filter(rsp_row, filter),
                        msg="Row with username %s should have been filtered: %s" % (rsp_row[username_key], filter))

    # All the usernames in exp_usernames should be in rsp_usernames except filtered ones
    missing_usernames = [username for username in exp_usernames if username not in rsp_usernames]
    if len(missing_usernames) > 0 and filter:
      # check if they have been filtered
      missing_usernames = [username for username in missing_usernames if self.matches_filter(exp_rows[username], filter)]
    self.assertSequenceEqual(missing_usernames, [], msg="Missing usernames %s in received CSV" % missing_usernames)

    # All the usernames in exp_usernames should be in rsp_usernames except self.member and self.superuser
    for unkown_username in [username for username in rsp_usernames if username not in exp_usernames]:
      self.assertIn(unkown_username, [self.member.username, self.superuser.username],
                    "Unknown username %s in received CSV" % unkown_username)

    # All the columns in exp_rows should be the same in rsp_rows
    for username, exp_row in exp_rows.items():
      if not self.matches_filter(exp_row, filter):
        continue
      rsp_row = rsp_rows[username]
      # avatar not exported, so ignore it
      wrong_columns = [key for key in exp_row.keys() if exp_row[key] != rsp_row[key] and key != "avatar"]
      self.assertSequenceEqual(wrong_columns, [],
                               "Wrong column %s for username %s" % (wrong_columns, username))
      # check that other columns are empty
      non_empty_columns = [key for key in rsp_row.keys() if key not in exp_csv.fieldnames and rsp_row[key] != '']
      self.assertSequenceEqual(non_empty_columns, [],
                               "Columns %s for username %s should be empty" % (non_empty_columns, username))

  def do_test_export(self, expected_filename, lang, filter=None):
    url = reverse('members:export_members_to_csv')
    if filter is None:
      filter = {}
    response = self.client.post(url, filter, follow=True, HTTP_ACCEPT_LANGUAGE=lang)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="members.csv"')
    self.assertEqual(response.get('Content-Type'), 'text/csv')
    response_content = response.content.decode('utf-8')
    # print("response_content=", response_content)
    rsp_csv = csv.DictReader(io.StringIO(response_content))
    with open(get_test_file(expected_filename)) as csvfile:
      exp_csv = csv.DictReader(csvfile)
      self.check_CSVs_are_equivalent(exp_csv, rsp_csv, filter)

  # force language to make sure the CSV fields are properly translated
  @translation.override('en-us')
  def test_export_en(self):
    self.do_test_import('import_members.csv', 'en-us', 4)
    self.do_test_export('import_members.csv', 'en-us')

  # force language to make sure the CSV fields are properly translated
  @translation.override('fr')
  def test_export_fr(self):
    self.do_test_import('import_members-fr.csv', 'fr', 4, member_prefix='member-fr')
    self.do_test_export('import_members-fr.csv', 'fr')

  @translation.override('en-us')
  def test_export_en_with_filter(self):
    self.do_test_import('import_members.csv', 'en-us', 4)
    self.do_test_export('import_members.csv', 'en-us', {'name-id': 'Doe'})
    self.do_test_export('import_members.csv', 'en-us', {'city-id': 'Liverpool'})
    self.do_test_export('import_members.csv', 'en-us', {'name-id': 'Doe'})
