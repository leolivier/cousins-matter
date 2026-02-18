from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRedirect
from cm_main.mixins import OnlyAdminMixin
from cm_main.utils import confirm_delete_modal
from .models import FlatPage
from .forms import PageForm


class PageCreateView(OnlyAdminMixin, generic.CreateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, *args, **kwargs):
    if not request.user.is_superuser:
      raise PermissionDenied
    form = PageForm(request.POST)
    if form.is_valid():
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


class PageTreeView(generic.ListView):
  model = FlatPage
  template_name = "pages/page_tree.html"


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
