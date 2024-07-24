from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site

from cm_main.views import OnlyAdminMixin
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
      page.save()
      return redirect(flatpage_url(page.url))
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
      return redirect(flatpage_url(page.url))

    return render(request, self.template_name, {'form': form})


class PageAdminListView(OnlyAdminMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/pages_admin_list.html"


class PageTreeView(OnlyAdminMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/page_tree.html"
