import logging
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRedirect

from cm_main.utils import check_edit_permission
from ..models import Gallery
from ..forms import GalleryForm

logger = logging.getLogger(__name__)


class GalleryCreateView(generic.CreateView):
  template_name = "galleries/gallery_form.html"
  model = Gallery
  form_class = GalleryForm

  def get(self, request, parent_gallery=None):
    if parent_gallery:
      self.initial.update({"parent": parent_gallery})
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
    gallery = super().get_object(**kwargs)
    if gallery.owner:
      check_edit_permission(self.request, gallery.owner)
    return gallery


class GalleryDetailView(generic.DetailView):
  template_name = "galleries/gallery_detail.html"
  model = Gallery
  fields = "__all__"

  def get(self, request, pk, page=1):  # TODO manage slug instead of pk
    # gallery = get_object_or_404(Gallery, pk=pk)
    gallery = Gallery.objects.select_related("owner").select_related("parent").get(pk=pk)
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
    galleries = Gallery.objects.filter(parent=None)
    return {"galleries": galleries}


def delete_gallery(request, pk):
  gallery = get_object_or_404(Gallery, pk=pk)
  if request.method == "POST":
    if gallery.owner:
      check_edit_permission(request, gallery.owner)
    gallery.delete()
    messages.success(request, _("Gallery deleted successfully"))
    return HttpResponseClientRedirect(reverse("galleries:galleries"))
  return render(
    request,
    "cm_main/common/confirm-delete-modal-htmx.html",
    {
      "ays_title": _("Delete gallery"),
      "ays_msg": _('Are you sure you want to delete "%(object)s" and all photos and sub galleries it contains?')
      % {"object": gallery.name},
      "delete_url": request.get_full_path(),
      "expected_value": gallery.name,
    },
  )
