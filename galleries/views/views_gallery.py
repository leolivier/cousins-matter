import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.http import Http404

from core.htmx import htmx_redirect
from core.utils import check_edit_permission, confirm_delete_modal
from ..models import Gallery
from ..forms import GalleryForm
from ..services import build_gallery_tree, get_gallery_detail_queryset

logger = logging.getLogger(__name__)


class GalleryCreateView(generic.CreateView):
  template_name = "galleries/gallery_form.html"
  model = Gallery
  form_class = GalleryForm

  def get(self, request, parent_gallery=None):
    if parent_gallery:
      # parent_gallery is a slug; fetch the actual object
      parent_obj = get_object_or_404(Gallery, slug=parent_gallery)
      self.initial.update({"parent": parent_obj.id})
    return super().get(request)

  def form_valid(self, form):
    form.instance.owner = self.request.user
    messages.success(self.request, _("Gallery created successfully"))
    return super().form_valid(form)


class GalleryUpdateView(generic.UpdateView):
  template_name = "galleries/gallery_form.html"
  model = Gallery
  form_class = GalleryForm

  def get_object(self, **kwargs):
    # retrieve by slug from URL
    slug = self.kwargs.get("slug", None)
    if slug is None:
      raise Http404("No gallery found matching the given slug.")
    gallery = get_object_or_404(Gallery, slug=slug)
    if gallery.owner:
      check_edit_permission(self.request, gallery.owner)
    return gallery


class GalleryDetailView(generic.DetailView):
  template_name = "galleries/gallery_detail.html"
  model = Gallery
  fields = "__all__"

  def get(self, request, slug, page=1):
    gallery = get_object_or_404(get_gallery_detail_queryset(), slug=slug)
    page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_GALLERY_PAGE_SIZE

    return render(
      request,
      self.template_name,
      context={"gallery": gallery, "page_num": page, "page_size": page_size},
    )

  # TODO: every member can edit any gallery ???


class GalleryTreeView(generic.ListView):
  template_name = "galleries/galleries_tree.html"
  model = Gallery

  def get_context_data(self, **kwargs):
    # Gallery tree: fetched and assembled in services to avoid recursive N+1 queries
    return {"galleries": build_gallery_tree()}


def delete_gallery(request, slug):
  gallery = get_object_or_404(Gallery, slug=slug)
  if request.method == "POST":
    if gallery.owner:
      check_edit_permission(request, gallery.owner)
    gallery.delete()
    messages.success(request, _("Gallery deleted successfully"))
    return htmx_redirect(reverse("galleries:galleries"))
  return confirm_delete_modal(
    request,
    _("Delete gallery"),
    _('Are you sure you want to delete "%(object)s" and all photos and sub galleries it contains?') % {"object": gallery.name},
    expected_value=gallery.name,
  )
