from django.template import Library
from ..models import Photo

register = Library()

# TODO: manage pagination
@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery):
  photos = Photo.objects.filter(gallery=gallery)
  return {"photos": photos, "gallery": gallery }

# TODO: manage pagination
@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False):
  return {
    "galleries": galleries if hasattr(galleries, '__iter__') else [galleries],
    "recursive": recursive,
  }

