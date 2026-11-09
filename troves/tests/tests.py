from django.urls import reverse
from django.utils.html import escape
from core.utils import (
  create_test_image,
  test_media_root_decorator,
  protected_media_url,
)
from members.tests.tests_member_base import MemberTestCase
from ..models import Trove


@test_media_root_decorator(__file__)
class TestTroveList(MemberTestCase):
  def setUp(self):
    self.treasures_data = [
      {
        "title": "title 1",
        "description": "Description 1",
        "picture": create_test_image(__file__, "test-image-1.jpg"),
        "category": "history",
        "owner": self.member,
      },
      {
        "title": "title 2",
        "description": "Description 2",
        "picture": create_test_image(__file__, "test-image-2.jpg"),
        "file": create_test_image(__file__, "test-image-3.jpg"),
        "category": "recipes",
        "owner": self.member,
      },
    ]
    self.treasures = []
    super().setUp()

  def tearDown(self):
    Trove.objects.all().delete()
    self.treasures = []
    return super().tearDown()

  def check_treasure(self, treasure, treasure_data):
    self.assertEqual(treasure.title, treasure_data["title"])
    self.assertEqual(treasure.description, treasure_data["description"])
    self.assertEqual(treasure.category, treasure_data["category"])
    self.assertEqual(treasure.owner, self.member)
    self.assertTrue(treasure.picture)
    # self.assertEqual(protected_media_url(treasure.picture.name), treasure_data['picture'].url)
    self.assertTrue(treasure.thumbnail)
    if "file" in treasure_data:
      self.assertTrue(treasure.file)
    else:
      self.assertFalse(treasure.file)

  def create_troves(self):
    for treasure_data in self.treasures_data:
      treasure = Trove.objects.create(**treasure_data)
      self.check_treasure(treasure, treasure_data)
      self.treasures.append(treasure)

  def check_treasure_in_response(self, treasure, response, is_detail=False):
    # Warning: this works only because there is only two objects and they are both in the same page
    self.assertContains(response, treasure.title)
    # the template renders the label with Django's autoescape: search the
    # escaped form, otherwise the assertion only passes for labels without '&'
    self.assertContains(response, escape(Trove.translate_category(treasure.category)))
    if treasure.file and not treasure.description:
      self.assertContains(response, protected_media_url(treasure.file.name))
    if is_detail:
      self.assertContains(response, treasure.description)
      self.assertContains(response, protected_media_url(treasure.picture.name))
      self.assertNotContains(response, protected_media_url(treasure.thumbnail.name))
      if treasure.file:
        self.assertContains(response, protected_media_url(treasure.file.name))
    else:
      self.assertContains(response, protected_media_url(treasure.thumbnail.name))
      if treasure.file and not treasure.description:
        self.assertNotContains(response, protected_media_url(treasure.file.name))
      else:
        self.assertContains(response, reverse("troves:detail", args=[treasure.id]))

  def test_create_troves(self):
    response = self.client.get(reverse("troves:create"), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "troves/treasure_form.html")

    for treasure_data in self.treasures_data:
      response = self.client.post(reverse("troves:create"), treasure_data, follow=True)
      self.assertEqual(response.status_code, 200)
      self.assertTemplateUsed(response, "troves/trove_cave.html")
      treasure = Trove.objects.get(title=treasure_data["title"])
      self.check_treasure(treasure, treasure_data)
      self.check_treasure_in_response(treasure, response)

  def test_trove_list(self):
    self.create_troves()
    response = self.client.get(reverse("troves:list"), follow=True)
    self.assertEqual(response.status_code, 200)
    for treasure in self.treasures:
      self.check_treasure_in_response(treasure, response)

  def test_modify_treasure(self):
    self.create_troves()
    treasure = self.treasures[0]
    updated_treasure_data = {
      "title": "new title",
      "description": "New Description",
      "picture": create_test_image(__file__, "test-image-3.jpg"),
      "category": "history",
      "owner": self.member,
    }

    response = self.client.get(reverse("troves:update", kwargs={"pk": treasure.id}), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "troves/treasure_form.html")
    self.assertContains(response, treasure.description, html=True)
    self.assertContains(response, Trove.translate_category(treasure.category), html=True)

    response = self.client.post(
      reverse("troves:update", kwargs={"pk": treasure.id}),
      updated_treasure_data,
      follow=True,
    )
    self.assertEqual(response.status_code, 200)
    # self.print_response(response)
    self.assertTemplateUsed(response, "troves/trove_cave.html")
    treasure = Trove.objects.get(id=treasure.id)
    self.check_treasure(treasure, updated_treasure_data)
    self.check_treasure_in_response(treasure, response)

  def test_treasure_detail(self):
    self.create_troves()
    treasures = Trove.objects.filter(file__isnull=True, description__isnull=False)
    for treasure in treasures:
      response = self.client.get(reverse("troves:detail", args=[treasure.id]), follow=True)
      self.assertEqual(response.status_code, 200)
      self.assertTemplateUsed(response, "troves/treasure_detail.html")
      self.check_treasure_in_response(treasure, response, True)

  def test_trove_cave_filter_by_category(self):
    self.create_troves()
    response = self.client.get(reverse("troves:list"), {"category": "history"}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "troves/trove_cave.html")
    self.assertContains(response, "title 1")  # history
    self.assertNotContains(response, "title 2")  # recipes

  def test_trove_cave_invalid_category(self):
    self.create_troves()
    response = self.client.get(reverse("troves:list"), {"category": "nonexistent"}, follow=True)
    self.assertEqual(response.status_code, 200)
    # Invalid category falls back to showing all treasures
    self.assertTemplateUsed(response, "troves/trove_cave.html")
    self.assertContains(response, "title 1")  # history
    self.assertContains(response, "title 2")  # recipes

  def test_trove_cave_page_out_of_bounds(self):
    self.create_troves()
    response = self.client.get(reverse("troves:page", args=[9999]))
    self.assertEqual(response.status_code, 302)
    response = self.client.get(reverse("troves:page", args=[9999]), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "troves/trove_cave.html")
    self.assertContains(response, "title 1")  # history
    self.assertContains(response, "title 2")  # recipes

  def test_delete_treasure(self):
    self.create_troves()
    treasure = self.treasures[0]
    response = self.client.delete(
      reverse("troves:delete", args=[treasure.id]),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertFalse(Trove.objects.filter(id=treasure.id).exists())

  def test_translate_category(self):
    from django.utils.translation import gettext as _

    result = Trove.translate_category("history")
    self.assertEqual(result, _("History & Stories"))

  def test_thumbnail_path(self):
    self.create_troves()
    treasure = self.treasures[0]
    path = treasure._thumbnail_path()
    self.assertIn(treasure.picture.name.split("/")[-1], path)


class TestTroveDetailSecurityAndUrl(MemberTestCase):
  """Stored-XSS sanitization of description/title and the external URL feature."""

  def setUp(self):
    super().setUp()
    self.treasure = Trove.objects.create(
      title="title 1",
      description="Description 1",
      picture=create_test_image(__file__, "test-image-1.jpg"),
      category="history",
      owner=self.member,
    )

  def tearDown(self):
    Trove.objects.all().delete()
    return super().tearDown()

  def test_detail_sanitizes_script_in_description(self):
    self.treasure.description = '<p>ok</p><script>alert(1)</script><img src=x onerror="alert(2)">'
    self.treasure.save()
    response = self.client.get(reverse("troves:detail", args=[self.treasure.id]))
    self.assertContains(response, "<p>ok</p>", status_code=200)
    self.assertNotContains(response, "<script>")
    self.assertNotContains(response, "onerror")

  def test_detail_sanitizes_legacy_stored_xss_in_title(self):
    # titles are plain text: the list template must escape them (regression test
    # for the autoescape-off rendering of trove_cave.html)
    Trove.objects.filter(id=self.treasure.id).update(title='x"><script>alert(1)</script>')
    response = self.client.get(reverse("troves:list"))
    # the payload must be rendered as escaped text, not executed
    self.assertNotContains(response, "<script>alert(1)</script>")
    self.assertContains(response, "x&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;")

  def test_youtube_url_is_embedded(self):
    for url in [
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "https://youtu.be/dQw4w9WgXcQ",
      "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    ]:
      self.treasure.url = url
      self.treasure.save()
      response = self.client.get(reverse("troves:detail", args=[self.treasure.id]))
      self.assertContains(response, "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ")

  def test_non_youtube_url_is_a_link(self):
    self.treasure.url = "https://example.com/page"
    self.treasure.save()
    response = self.client.get(reverse("troves:detail", args=[self.treasure.id]))
    self.assertNotIn("<iframe", str(response.content))
    self.assertContains(response, "https://example.com/page")
