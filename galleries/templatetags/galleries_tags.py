from django.template import Library
from django.urls import reverse
from cousinsmatter.utils import Paginator
from ..models import Photo

register = Library()


@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery, page_num, page_size):
  photos = Photo.objects.filter(gallery=gallery)
  ptor = Paginator(photos, page_size, compute_link=lambda page: reverse('galleries:detail_page', args=[gallery.id, page]))
  page = ptor.get_page_data(page_num)
  return {"page": page}


@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False):
  return {
    "galleries": galleries if hasattr(galleries, '__iter__') else [galleries],
    "recursive": recursive,
  }
