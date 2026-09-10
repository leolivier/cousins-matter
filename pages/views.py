from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django_htmx.http import HttpResponseClientRedirect

from core.mixins import OnlyAdminMixin
from core.utils import confirm_delete_modal

from .forms import PageForm
from .models import FlatPage

DEFAULT_TEMPLATE = "flatpages/default.html"


def flatpage(request, url):
  """Tenant-aware replacement for django.contrib.flatpages' fallback view.

  Same behavior as the stock view, but resolves the page through the
  scoped ``pages.FlatPage`` manager, so a family can never read another
  family's pages. Serves ``<PAGES_URL_PREFIX><url>`` and, through
  ``TenantFlatpageFallbackMiddleware``, the raw page URL on 404s.
  """
  if not url.startswith("/"):
    url = "/" + url
  try:
    page = get_object_or_404(FlatPage, url=url)
  except Http404:
    if not url.endswith("/") and settings.APPEND_SLASH:
      page = get_object_or_404(FlatPage, url=f"{url}/")
      # request.path is user-controlled; a planted page (no url validator) with a
      # protocol-relative url like "//host/x/" would make this a redirect off-site
      target = f"{request.path}/"
      if not url_has_allowed_host_and_scheme(target, allowed_hosts=None):
        raise Http404
      return HttpResponsePermanentRedirect(target)
    raise
  return render_flatpage(request, page)


@csrf_protect
def render_flatpage(request, page):
  # If registration is required for accessing this page, and the user isn't
  # logged in, redirect to the login page.
  if page.registration_required and not request.user.is_authenticated:
    from django.contrib.auth.views import redirect_to_login

    return redirect_to_login(request.path)
  if page.template_name:
    template = loader.select_template((page.template_name, DEFAULT_TEMPLATE))
  else:
    template = loader.get_template(DEFAULT_TEMPLATE)
  # To avoid having to always use the "|safe" filter in flatpage templates,
  # mark the title and content as already safe (since they are raw HTML
  # content in the first place).
  page.title = mark_safe(page.title)  # nosec (stock flatpages: raw HTML by design)
  page.content = mark_safe(page.content)  # nosec (stock flatpages: raw HTML by design)
  return HttpResponse(template.render({"flatpage": page}, request))


class PageCreateView(OnlyAdminMixin, generic.CreateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, *args, **kwargs):
    if not request.user.is_superuser:
      raise PermissionDenied
    form = PageForm(request.POST)
    if form.is_valid():
      # atomic: the page is never left created without its site association
      with transaction.atomic():
        page = form.save()
        page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
        page.updated = True
        page.save()
      if "save" in request.POST:
        return redirect(page.url)
      elif "save-and-continue" in request.POST:
        messages.success(request, _('Page "%(title)s" saved') % {"title": page.title})
      else:
        raise ValueError("Unexpected button: {}".format(request.POST))
    return render(request, self.template_name, {"form": form})


class PageUpdateView(OnlyAdminMixin, generic.UpdateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, pk, *args, **kwargs):
    if not request.user.is_superuser:
      raise PermissionDenied
    page = get_object_or_404(FlatPage, pk=pk)
    form = PageForm(request.POST, instance=page)
    if form.is_valid():
      # atomic: the content and the "updated" flag commit together, so a later import of
      # predefined pages can never silently overwrite an unflagged edit
      with transaction.atomic():
        page = form.save()
        page.updated = True
        page.save(update_fields=["updated"])
      if "save" in request.POST:
        return redirect(page.url)
      elif "save-and-continue" in request.POST:
        messages.success(request, _('Page "%(title)s" saved') % {"title": page.title})
      else:
        raise ValueError("Unexpected button: {}".format(request.POST))
    return render(request, self.template_name, {"form": form})


class PageAdminListView(OnlyAdminMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/pages_admin_list.html"
  queryset = FlatPage.objects.prefetch_related("sites")


class PageTreeView(generic.ListView):
  model = FlatPage
  template_name = "pages/page_tree.html"
  queryset = FlatPage.objects.prefetch_related("sites")


class PageDeleteView(OnlyAdminMixin, generic.View):
  def post(self, request, pk):
    if not request.user.is_superuser:
      raise PermissionDenied
    page = get_object_or_404(FlatPage, pk=pk)
    page.delete()
    messages.success(request, _('Page "%(title)s" deleted') % {"title": page.title})
    return HttpResponseClientRedirect(reverse("pages-edit:edit_list"))

  def get(self, request, pk):
    page = get_object_or_404(FlatPage, pk=pk)
    delete_title = _("Delete Page")
    delete_msg = _('Are you sure you want to delete the page "%(title)s"?') % {"title": page.title}
    return confirm_delete_modal(request, delete_title, delete_msg)
