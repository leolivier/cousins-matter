from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.sites.models import Site

from cousinsmatter.utils import redirect_to_referer
from .forms import PageForm


class PageCreateView(LoginRequiredMixin, generic.CreateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def post(self, request, *args, **kwargs):
    form = PageForm(request.POST)
    if form.is_valid():
      page = form.save()
      page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
      page.save()
      return redirect(page.url)
    return render(request, self.template_name, {'form': form})


class PageUpdateView(LoginRequiredMixin, generic.UpdateView):
  template_name = "pages/page_form.html"
  model = FlatPage
  form_class = PageForm

  def _get_object(self, url):
    url = url.replace('//', '/')
    if not url.endswith('/'):
      url += '/'
    return get_object_or_404(FlatPage, url=url)

  def get_object(self):
    return self._get_object(self.kwargs['page_url'])

  def post(self, request, page_url, *args, **kwargs):
    page = self._get_object(page_url)
    form = PageForm(request.POST, instance=page)
    if form.is_valid():
      page = form.save()
      return redirect(page.url)

    for error in form.errors.values():
      messages.error(request, error)
    return redirect_to_referer(request)


class PageListView(LoginRequiredMixin, generic.ListView):
  model = FlatPage
  template_name = "pages/pages_list.html"
