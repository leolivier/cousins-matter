from django.urls import reverse
from django.utils.translation import gettext as _

from cm_main.templatetags.cm_tags import icon
from members.tests.tests_member_base import MemberTestCase
from ..forms import PageForm
from ..models import FlatPage
from .test_base import BasePageTestCase, TestPageMixin


class TestCreatePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_create_page(self):
    "Tests creating a page with valid data as superuser."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    response = self.client.get(reverse("pages-edit:create"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "pages/page_form.html")
    self._test_create_page()
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user

  def test_create_and_continue_page(self):
    "Tests creating a page with valid data as superuser and continue editing."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    response = self.client.get(reverse("pages-edit:create"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "pages/page_form.html")
    new_page_data = {
      "url": self.page_data["url"],
      "title": self.page_data["title"],
      "content": self.page_data["content"],
      "save-and-continue": "true",
    }
    self._test_create_page(new_page_data)
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user

  def test_url_checks_with_other_pages(self):
    "Tests that we cannot create 2 pages with the same url or a sub url of another page."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first create one page
    self._test_create_page()
    # then try to create another one with the same url
    new_page_data = {"url": self.page_data["url"], "title": "another title", "content": "another content", "save": "true"}
    form = PageForm(new_page_data)
    self.assertFormError(form, "url", [_("Flatpage with url %(url)s already exists") % {"url": new_page_data["url"]}])
    # now, try to create with "sub url"
    url = self.page_data["url"]
    form = PageForm({"url": f"{url}/3rd-title/", "title": "3rd title", "content": "3rd content", "save": "true"})
    self.assertFormError(form, "url", [_("A flatpage cannot be a subpage of another flatpage, check your URLs")])
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user


class TestUpdatePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_update_page(self):
    "Tests updating a page with valid data as superuser."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first create it
    page = self._test_create_page()
    # now try to update it
    new_page_data = {
      "url": "/another-level/another-title/",
      "title": "another title",
      "content": "another content",
      "save": "true",
    }
    response = self.client.post(reverse("pages-edit:update", args=[page.id]), new_page_data, follow=True)
    self.assertEqual(response.status_code, 200)
    page.refresh_from_db()
    self.assertEqual(page.url, new_page_data["url"])
    self.assertEqual(page.title, new_page_data["title"])
    self.assertEqual(page.content, new_page_data["content"])
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user

  def test_update_and_continue_page(self):
    "Tests updating a page with valid data as superuser and continue editing."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first create it
    page = self._test_create_page()
    # now try to update it
    new_page_data = {
      "url": "/another-level/another-title/",
      "title": "another title",
      "content": "another content",
      "save-and-continue": "true",
    }
    response = self.client.post(reverse("pages-edit:update", args=[page.id]), new_page_data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "pages/page_form.html")
    page.refresh_from_db()
    self.assertEqual(page.url, new_page_data["url"])
    self.assertEqual(page.title, new_page_data["title"])
    self.assertEqual(page.content, new_page_data["content"])
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user

  def test_same_url(self):
    "Tests updating a page with the same url as another page."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first create 2 pages with different urls
    page1 = self._test_create_page()
    # 2nd page
    new_page_data = {
      "url": "/another-level/another-title/",
      "title": "another title",
      "content": "another content",
      "save": "true",
    }
    page2 = self._test_create_page(new_page_data)

    # Now try to update page 2 with the same url with the same URL as page1
    new_page_data["url"] = page1.url
    new_page_data["id"] = page2.id
    form = PageForm(new_page_data)
    self.assertFormError(form, "url", [_("Flatpage with url %(url)s already exists") % {"url": new_page_data["url"]}])
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user


class TestDisplayPageList(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_display_page(self):
    "Tests displaying a list of pages."
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first create 2 pages with different urls
    page1 = self._test_create_page()
    # 2nd page
    new_page_data = {
      "url": "/another-level/another-title/",
      "title": "another title",
      "content": "another content",
      "save": "true",
    }
    page2 = self._test_create_page(new_page_data)
    # now, display them
    response = self.client.get(reverse("pages-edit:edit_list"))
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    for page in [page1, page2]:
      self.assertContains(
        response,
        f'''
  <div class="panel-block">
    <a href="{reverse("pages-edit:update", args=[page.id])}">
      {icon("edit-page", "panel-icon")}
      {page.url}
    </a>
    &nbsp;&nbsp;&nbsp;-&nbsp;&nbsp;&nbsp;<strong>{page.title}</strong>
  </div>''',
        html=True,
      )

    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user


class TestDeletePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_delete_page(self):
    "Tests deleting a page."
    # get the # of pages at start
    npages = FlatPage.objects.count()
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    # first, create a page
    page = self._test_create_page()
    self.assertEqual(FlatPage.objects.filter(url=page.url).count(), 1)
    self.assertEqual(FlatPage.objects.count(), npages + 1)
    # now, delete it
    response = self.client.post(reverse("pages-edit:delete", args=[page.id]), follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(FlatPage.objects.count(), npages)
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user
