from datetime import date
import logging
from django.forms import ValidationError
from django_htmx.http import HttpResponseClientRedirect
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext as _
from cm_main.utils import check_edit_permission
from ..models import Photo
from ..forms import PhotoForm

logger = logging.getLogger(__name__)


def get_next_prev_photo(pk, side):
  # this raises an exception Photo.DoesNotExist if the photo doesn't exist
  gallery_id = Photo.objects.only("gallery_id").get(pk=pk).gallery_id
  photo = Photo.objects.filter(gallery=gallery_id).order_by("id")

  match side:
    case "prev":
      photo = photo.filter(id__lt=pk).last()
    case "next":
      photo = photo.filter(id__gt=pk).first()
    case None:
      photo = photo.get(id=pk)
    case _:
      raise ValueError("Invalid side: %s" % side)

  return photo or Photo.objects.get(id=pk)


class PhotoDetailView(generic.DetailView):
  template_name = "galleries/photo_detail.html"
  model = Photo


def get_fullscreen_photo(request, pk):
  assert request.htmx
  try:
    photo = get_next_prev_photo(pk, request.GET.get("side"))
  except Photo.DoesNotExist:
    messages.error(request, _("Photo not found"))
    return HttpResponseClientRedirect(reverse("galleries:galleries"))

  return render(
    request,
    "galleries/photo_fullscreen_htmx.html#image",
    {
      "swipe_url": reverse("galleries:get_fullscreen_photo", args=[photo.id]),
      "fullscreen_url": photo.image.url,
      "pk": photo.id,
    },
  )


class PhotoAddView(generic.CreateView):
  template_name = "galleries/photo_form.html"
  model = Photo
  form_class = PhotoForm

  def post(self, request, gallery, *args, **kwargs):
    form = PhotoForm(request.POST, request.FILES)
    if form.is_valid():
      try:  # issue 120: if any exception during the thumbnail creation process, remove the photo from the database
        form.instance.uploaded_by = self.request.user
        photo = form.save()
        if "create-and-add" in request.POST:
          messages.success(request, _("Photo created"))
          return redirect("galleries:add_photo", gallery)
        else:
          return redirect("galleries:photo", photo.id)
      except (ValidationError, PermissionDenied, PermissionError) as e:
        logger.error(e)
        messages.error(request, _("Error when creating this photo: %s.") % str(e))
        return render(request, self.template_name, {"form": form})
    else:
      return render(request, self.template_name, {"form": form})

  def get(self, request, gallery):
    # initialize gallery to the value in the url and current date
    form = PhotoForm(initial={"gallery": gallery, "date": date.today()})
    return render(request, self.template_name, {"form": form})


class PhotoEditView(generic.UpdateView):
  template_name = "galleries/photo_form.html"
  model = Photo
  form_class = PhotoForm

  def form_valid(self, form):
    if self.object.uploaded_by:
      check_edit_permission(self.request, self.object.uploaded_by)
    elif self.object.gallery.owner:
      check_edit_permission(self.request, self.object.gallery.owner)
    messages.success(self.request, _("Photo updated successfully"))
    return super().form_valid(form)


def delete_photo(request, pk):
  try:
    photo = Photo.objects.select_related("gallery").get(pk=pk)
  except Photo.DoesNotExist:
    return HttpResponseClientRedirect(reverse("galleries:galleries"), status=404)
  if not (
    request.user.is_superuser
    or (photo.uploaded_by and request.user == photo.uploaded_by)
    or (photo.gallery.owner and request.user == photo.gallery.owner)
  ):
    raise PermissionDenied
  if request.method == "POST":
    photo.delete()
    messages.success(request, _("Photo deleted"))
    return HttpResponseClientRedirect(reverse("galleries:detail", args=[photo.gallery.id]))
  delete_title = _("Delete photo")
  delete_msg = _('Are you sure you want to delete "%(object)s"?') % {"object": photo.name}
  return render(
    request,
    "cm_main/common/confirm-delete-modal-htmx.html",
    {
      "ays_title": delete_title,
      "button_text": "",
      "ays_msg": delete_msg,
      "delete_url": request.get_full_path(),
      "expected_value": photo.name,
    },
  )
