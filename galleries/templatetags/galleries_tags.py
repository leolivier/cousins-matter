from django.template import Library
from django.core.paginator import Paginator
from ..models import Photo

register = Library()


# TODO: manage pagination
@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery, page_num, page_size):
  photos = Photo.objects.filter(gallery=gallery)
  ptor = Paginator(photos, page_size)
  max_pages = 5
  # compute a page range from the initial range + or -max-pages
  page_range = ptor.page_range[max(0, page_num-max_pages-1):min(ptor.num_pages+1, page_num+max_pages)]
  page = ptor.page(page_num)
  return {
          "page": page,
          "page_range": page_range,
          "current_page": page_num,
          "num_pages": ptor.num_pages,
          "gallery": gallery}

# TODO: manage pagination


@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False):
  return {
    "galleries": galleries if hasattr(galleries, '__iter__') else [galleries],
    "recursive": recursive,
  }
