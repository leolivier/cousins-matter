import logging
from django.conf import settings
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRedirect
from django.http import Http404

from core.utils import check_edit_permission, confirm_delete_modal
from ..models import Gallery
from ..forms import GalleryForm

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
    gallery = (
      Gallery.objects
      .select_related("owner", "parent", "cover")
      .annotate(photo_count=Count("photo"))
      .prefetch_related(Prefetch("children", queryset=Gallery.objects.select_related("cover")))
      .get(slug=slug)
    )
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
    # Fetch all galleries in a single query with cover prefetched and photo count annotated
    all_galleries = list(Gallery.objects.select_related("cover").annotate(photo_count=Count("photo")).order_by("name"))

    # Build the tree in Python to avoid recursive N+1 queries
    by_id = {g.pk: g for g in all_galleries}
    for g in all_galleries:
      g.cached_children = []
    roots = []
    for g in all_galleries:
      if g.parent_id and g.parent_id in by_id:
        by_id[g.parent_id].cached_children.append(g)
      elif not g.parent_id:
        roots.append(g)

    return {"galleries": roots}


def delete_gallery(request, slug):
  gallery = get_object_or_404(Gallery, slug=slug)
  if request.method == "POST":
    if gallery.owner:
      check_edit_permission(request, gallery.owner)
    gallery.delete()
    messages.success(request, _("Gallery deleted successfully"))
    return HttpResponseClientRedirect(reverse("galleries:galleries"))
  return confirm_delete_modal(
    request,
    _("Delete gallery"),
    _('Are you sure you want to delete "%(object)s" and all photos and sub galleries it contains?') % {"object": gallery.name},
    expected_value=gallery.name,
  )
