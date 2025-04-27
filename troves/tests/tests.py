from django.urls import reverse
from cm_main.utils import create_test_image, test_media_root_decorator
from members.tests.tests_member_base import MemberTestCase
from ..models import Trove


@test_media_root_decorator(__file__)
class TestTroveList(MemberTestCase):
  def setUp(self):
    self.treasures_data = [
      {
        'description': 'Description 1',
        'picture': create_test_image(__file__, "test-image-1.jpg"),
        'category': 'history',
        'owner': self.member,
      },
      {
        'description': 'Description 2',
        'picture': create_test_image(__file__, "test-image-2.jpg"),
        'file': create_test_image(__file__, "test-image-3.jpg"),
        'category': 'recipes',
        'owner': self.member,
      },
    ]
    self.treasures = []
    super().setUp()

  def tearDown(self):
    Trove.objects.all().delete()
    self.treasures = []
    return super().tearDown()

  def check_treasure(self, treasure, treasure_data):
    self.assertEqual(treasure.description, treasure_data['description'])
    self.assertEqual(treasure.category, treasure_data['category'])
    self.assertEqual(treasure.owner, self.member)
    self.assertTrue(treasure.picture)
    # self.assertEqual(treasure.picture.url, treasure_data['picture'].url)
    self.assertTrue(treasure.thumbnail)
    if 'file' in treasure_data:
      self.assertTrue(treasure.file)
    else:
      self.assertFalse(treasure.file)

  def create_troves(self):
    for treasure_data in self.treasures_data:
      treasure = Trove.objects.create(**treasure_data)
      self.check_treasure(treasure, treasure_data)
      self.treasures.append(treasure)

  def check_treasure_in_response(self, treasure, response):
    # Warning: this works only because there is only two objects and they are both in the same page
    self.assertContains(response, treasure.description)
    self.assertContains(response, Trove.translate_category(treasure.category))
    self.assertContains(response, treasure.thumbnail.url)
    if treasure.file:
      self.assertContains(response, treasure.file.url)
      self.assertNotContains(response, treasure.picture.url)
    else:
      self.assertContains(response, treasure.picture.url)

  def test_create_troves(self):
    response = self.client.get(reverse('troves:create'), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'troves/treasure_form.html')

    for treasure_data in self.treasures_data:
      response = self.client.post(reverse('troves:create'), treasure_data, follow=True)
      self.assertEqual(response.status_code, 200)
      self.assertTemplateUsed(response, 'troves/trove_cave.html')
      treasure = Trove.objects.get(description=treasure_data['description'])
      self.check_treasure(treasure, treasure_data)
      self.check_treasure_in_response(treasure, response)

  def test_trove_list(self):
    self.create_troves()
    response = self.client.get(reverse('troves:list'), follow=True)
    self.assertEqual(response.status_code, 200)
    for treasure in self.treasures:
      self.check_treasure_in_response(treasure, response)

  def test_modify_treasure(self):
    self.create_troves()
    treasure = self.treasures[0]
    updated_treasure_data = {
        'description': 'New Description',
        'picture': create_test_image(__file__, "test-image-3.jpg"),
        'category': 'history',
        'owner': self.member,
      }

    response = self.client.get(reverse('troves:update', kwargs={'pk': treasure.id}), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'troves/treasure_form.html')
    self.assertContains(response, treasure.description, html=True)
    self.assertContains(response, Trove.translate_category(treasure.category), html=True)

    response = self.client.post(reverse('troves:update', kwargs={'pk': treasure.id}),
                                updated_treasure_data, follow=True)
    self.assertEqual(response.status_code, 200)
    # self.print_response(response)
    self.assertTemplateUsed(response, 'troves/trove_cave.html')
    treasure = Trove.objects.get(id=treasure.id)
    self.check_treasure(treasure, updated_treasure_data)
    self.check_treasure_in_response(treasure, response)
