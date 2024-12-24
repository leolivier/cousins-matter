from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.utils.translation import gettext as _

from cm_main.views.views_general import OnlyAdminMixin
from .models import FlatPage
from .utils import flatpage_url
from .forms import PageForm


class PageCreateView(OnlyAdminMixin, generic.CreateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, *args, **kwargs):
    form = PageForm(request.POST)
    if form.is_valid():
      page = form.save()
      page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
      page.updated = True
      page.save()
      if 'save' in request.POST:
        return redirect(flatpage_url(page.url))
      elif 'save-and-continue' in request.POST:
        messages.success(request, _("Page \"%(title)s\" saved") % {"title": page.title})
      else:
        raise ValueError("Unexpected button: {}".format(request.POST))
    return render(request, self.template_name, {'form': form})


class PageUpdateView(OnlyAdminMixin, generic.UpdateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, pk, *args, **kwargs):
    page = get_object_or_404(FlatPage, pk=pk)
    form = PageForm(request.POST, instance=page)
    if form.is_valid():
      page = form.save()
      page.updated = True
      page.save(update_fields=['updated'])
      if 'save' in request.POST:
        return redirect(flatpage_url(page.url))
      elif 'save-and-continue' in request.POST:
        messages.success(request, _("Page \"%(title)s\" saved") % {"title": page.title})
      else:
        raise ValueError("Unexpected button: {}".format(request.POST))
    return render(request, self.template_name, {'form': form})


class PageAdminListView(OnlyAdminMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/pages_admin_list.html"


class PageTreeView(LoginRequiredMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/page_tree.html"


class PageDeleteView(OnlyAdminMixin, generic.View):

  def get(self, request, pk):
    page = get_object_or_404(FlatPage, pk=pk)
    page.delete()
    messages.success(request, _("Page \"%(title)s\" deleted") % {"title": page.title})
    return redirect("pages-edit:edit_list")
