from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import translation
from datetime import date
from ..models import ALL_FIELD_NAMES, MANDATORY_FIELD_NAMES, Member
from .tests_member import MemberTestCase
from ..views.views_import import CSVImportView
import os


def get_test_file(filename):
  return os.path.join(os.path.dirname(__file__), 'resources', filename)


class TestMemberImport(MemberTestCase):

  def test_get_import(self):
    response = self.client.get(reverse('members:csv_import'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/import_members.html')
    self.assertIs(response.resolver_match.func.view_class, CSVImportView)

  def do_upload_file(self, file, lang):
    url = reverse('members:csv_import')
    csv_file = get_test_file(file)
    # force language to make sure the CSV fields are ok
    with translation.override(lang):
      response = self.client.post(url,
                                  {'csv_file': SimpleUploadedFile(file,
                                                                  open(csv_file, 'rb').read(),
                                                                  content_type='text/csv')}, follow=True)
    # print(response.content)
    return response

  def do_test_import(self, file, lang, expected_num):
    prev_num = Member.objects.count()
    response = self.do_upload_file(file, lang)
    self.assertEqual(response.status_code, 200)
    # Check that expected_num members were imported
    self.assertEqual(Member.objects.count(), prev_num+expected_num)
    # Check that specific members were created
    self.assertTrue(Member.objects.filter(account__first_name='John', account__last_name='Doe').exists())
    self.assertTrue(Member.objects.filter(account__email='member2@test.com').exists())
    self.assertTrue(Member.objects.filter(address__city='Blackpool').exists())
    self.assertTrue(Member.objects.filter(birthdate=date(2000, 1, 3)).exists())

  def test_import_en(self):
    self.do_test_import('import_members.csv', 'en-US', 4)

  def test_import_fr(self):
    self.do_test_import('import_members-fr.csv', 'fr-FR', 4)

  def test_wrong_field(self):
    response = self.do_upload_file('import_members-wrong-field.csv', 'en-US')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, f'''<li class="message is-error">
  <div class="message-body">
    {f'Unknown column in CSV file: "citi". Valid fields are {", ".join([str(s) for s in ALL_FIELD_NAMES.keys()])}'}
  </div>
</li>''', html=True)

  def test_missing_field(self):
    response = self.do_upload_file('import_members-missing-field.csv', 'en-US')
    self.assertEqual(response.status_code, 200)
    m_fields = ", ".join([str(s) for s in MANDATORY_FIELD_NAMES.keys()])
    self.assertContains(response, f'''<li class="message is-error">
  <div class="message-body">
    {f'Missing column in CSV file: "first_name". Mandatory fields are {m_fields}'}
  </div>
</li>''', html=True)
