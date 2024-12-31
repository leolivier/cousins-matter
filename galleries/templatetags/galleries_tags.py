from django.conf import settings
from django.db.models import Value, CharField, Case, When, F
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Concat
from django.template import Library
from django.urls import reverse
from cousinsmatter.utils import Paginator
from ..models import Photo

register = Library()


def get_gallery_photos(gallery):
  """Helper function returning all the photos in a gallery, including the previous and next photo urls in each photo"""
  previous_photo = Photo.objects.filter(
    id__lt=OuterRef('id'),
    gallery=gallery
  ).order_by('-id').values('id', 'image')[:1]

  next_photo = Photo.objects.filter(
    id__gt=OuterRef('id'),
    gallery=gallery
  ).order_by('id').values('id', 'image')[:1]

  return Photo.objects.filter(gallery=gallery).annotate(
    previous_url_short=Subquery(
        previous_photo.values('image')
    ),
    previous_id=Subquery(
        previous_photo.values('id')
    ),
    previous_url=Case(
        When(previous_url_short__isnull=False, 
             then=Concat(Value(settings.MEDIA_URL), F('previous_url_short'), output_field=CharField())),
        default=Value(None)
    ),
    next_url_short=Subquery(
        next_photo.values('image')
    ),
    next_id=Subquery(
        next_photo.values('id')
    ),
    next_url=Case(
        When(next_url_short__isnull=False, 
             then=Concat(Value(settings.MEDIA_URL), F('next_url_short'), output_field=CharField())),
        default=Value(None)
    )
  )


@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery, page_num, page_size):
  photos = get_gallery_photos(gallery)
  # print('query: ', photos.query)
  ptor = Paginator(photos, page_size, compute_link=lambda page: reverse('galleries:detail_page', args=[gallery.id, page]))
  if page_num > ptor.num_pages:
    page_num = ptor.num_pages
  page = ptor.get_page_data(page_num)
  return {"page": page}


@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False):
  return {
    "galleries": galleries if hasattr(galleries, '__iter__') else [galleries],
    "recursive": recursive,
  }
