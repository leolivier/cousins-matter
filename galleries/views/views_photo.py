from datetime import date
import logging
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from ..models import Photo
from ..forms import PhotoForm

logger = logging.getLogger(__name__)


class PhotoDetailView(LoginRequiredMixin, generic.DetailView):
  template_name = "galleries/photo_detail.html"
  model = Photo

  # TODO: all this is probably vastly inefficient!
  def get_queryset(self):
    if 'pk' not in self.kwargs:
      gallery = self.kwargs['gallery']
      ptor = Paginator(Photo.objects.filter(gallery=gallery), 1)
      photo_num = self.kwargs['photo_num'] if 'photo_num' in self.kwargs else 1
      page = ptor.page(photo_num)
      photo = page.object_list[0]
      self.kwargs['pk'] = photo.id
    return Photo.objects.filter(pk=self.kwargs['pk'])

  def get_context_data(self, object):
    return self.get_context_data_by_page_number(object) if 'photo_num' in self.kwargs else self.get_context_data_by_pk(object)

  def get_context_data_by_pk(self, photo):
    pk = self.kwargs['pk']
    # photo = get_object_or_404(Photo, pk=pk)
    gallery = photo.gallery
    photo_num = 0
    for id in Photo.objects.filter(gallery=gallery).values('id'):
      photo_num += 1
      if id['id'] == pk:
        break
    # no need to check if found as we did a get_object_or_404 above
    self.kwargs['gallery'] = gallery
    self.kwargs['photo_num'] = photo_num
    return self.get_context_data_by_page_number(photo)

  def get_context_data_by_page_number(self, photo):
    gallery = self.kwargs['gallery']
    ptor = Paginator(Photo.objects.filter(gallery=gallery), 1)
    photo_num = self.kwargs['photo_num'] if 'photo_num' in self.kwargs else 1
    page = ptor.page(photo_num)
    # photo = page.object_list[0]
    max_links = 5
    photo_range = ptor.page_range[max(0, photo_num-max_links-1):min(ptor.num_pages+1, photo_num+max_links)]
    return {
      'photo': photo,
      'page': page,
      "photo_range": photo_range,
      "current_photo": photo_num,
      "num_photos": ptor.num_pages,
    }


class PhotoAddView(LoginRequiredMixin, generic.CreateView):
  template_name = "galleries/add_photo.html"
  model = Photo
  form_class = PhotoForm

  def post(self, request: HttpRequest, gallery, *args, **kwargs) -> HttpResponse:
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
