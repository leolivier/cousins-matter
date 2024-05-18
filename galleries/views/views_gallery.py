import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from ..models import Gallery
from ..forms import GalleryForm

logger = logging.getLogger(__name__)


class GalleryCreateView(LoginRequiredMixin, generic.CreateView):

  template_name = "galleries/create_gallery.html"
  model = Gallery
  form_class = GalleryForm

  def get(self, request, parent_gallery=None):
    if parent_gallery:
      self.initial.update({'parent': parent_gallery})
    return super().get(request)


class GalleryUpdateView(LoginRequiredMixin, generic.UpdateView):

  template_name = "galleries/edit_gallery.html"
  model = Gallery
  form_class = GalleryForm


class GalleryDetailView(LoginRequiredMixin, generic.DetailView):
  template_name = "galleries/gallery_detail.html"
  model = Gallery
  fields = "__all__"

  def get(self, request, pk, page=1):  # TODO manage slug instead of pk
    gallery = get_object_or_404(Gallery, pk=pk)
    page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_GALLERY_PAGE_SIZE
    possible_page_sizes = [10, 25, 50, 100]
    if page_size not in possible_page_sizes:
      possible_page_sizes = sorted(possible_page_sizes + [int(page_size)])

    return render(request, self.template_name, context={"gallery": gallery, 
                                                        "page": page, 
                                                        "page_size": page_size, 
                                                        "possible_page_sizes": possible_page_sizes})


class GalleryTreeView(LoginRequiredMixin, generic.ListView):
  template_name = "galleries/galleries_tree.html"
  model = Gallery

  def get_context_data(self, **kwargs):
    galleries = Gallery.objects.filter(parent=None)
    return {"galleries": galleries}


@login_required
def delete_gallery(request, pk):
  gallery = get_object_or_404(Gallery, pk=pk)
  gallery.delete()
  messages.success(request, _("Gallery deleted"))
  return redirect("galleries:galleries")
