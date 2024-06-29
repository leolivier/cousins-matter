from datetime import date
import logging
from django.forms import ValidationError
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator as BasePaginator
from cousinsmatter.utils import Paginator
from ..models import Photo
from ..forms import PhotoForm

logger = logging.getLogger(__name__)


class PhotoDetailView(LoginRequiredMixin, generic.DetailView):
  template_name = "galleries/photo_detail.html"
  model = Photo

  def get(self, request, **kwargs):
    """This method can be called either with a photo id, or with a gallery id and a photo number in the gallery
    (if photo num not given, it takes the first one)"""
    if 'pk' not in kwargs:
      # if we don't have the pk in args, let's find the proper photo based on the photo_num in the gallery
      # using the BasePaginator ==> we try to find which photo is contained in the page, and use its pk
      if 'gallery' not in kwargs:
        raise ValidationError(_("Missing either photo id or gallery id"))
      gallery_id = kwargs['gallery']
      photo_num = kwargs['photo_num'] if 'photo_num' in kwargs else 1
      ptor = BasePaginator(Photo.objects.filter(gallery=gallery_id), 1)
      page = ptor.page(photo_num)
      # only one photo in the page, take it
      photo = page.object_list[0]
    else:
      # we have the pk in the args, now compute the gallery and photo num
      pk = kwargs['pk']
      photo = Photo.objects.get(pk=pk)
      gallery_id = photo.gallery.id
      photo_num = 0
      found = False
      for id in Photo.objects.filter(gallery=gallery_id).values('id'):
        photo_num += 1
        if id['id'] == pk:
          found = True
          break
      if not found:
        raise ValueError(_("Photo not found on that page"))

    # Now, we have everything, we can repaginate

    ptor = Paginator(Photo.objects.filter(gallery=gallery_id), 1,
                     compute_link=lambda photo_num: reverse("galleries:photo_list", args=[gallery_id, photo_num]))
    page = ptor.get_page_data(photo_num)
    return render(request, self.template_name, {'page': page})


class PhotoAddView(LoginRequiredMixin, generic.CreateView):
  template_name = "galleries/add_photo.html"
  model = Photo
  form_class = PhotoForm

  def post(self, request, gallery, *args, **kwargs):
    form = PhotoForm(request.POST, request.FILES)
    if form.is_valid():
      photo = form.save()
      if 'create-and-add' in request.POST:
        messages.success(request, _("Photo created"))
        return redirect("galleries:add_photo", gallery)
      else:
        return redirect("galleries:photo", photo.id)

  def get(self, request, gallery):
    # initialize gallery to the value in the url and current date
    form = PhotoForm(initial={'gallery': gallery, 'date': date.today()})
    return render(request, self.template_name, {'form': form})


class PhotoEditView(LoginRequiredMixin, generic.UpdateView):
  template_name = "galleries/edit_photo.html"
  model = Photo
  form_class = PhotoForm


@login_required
def delete_photo(request, pk):
  photo = get_object_or_404(Photo, pk=pk)
  gallery = photo.gallery.id
  photo.delete()
  messages.success(request, _("Photo deleted"))
  return redirect("galleries:detail", gallery)
