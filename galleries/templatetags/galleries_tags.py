from django.conf import settings
from django.db.models import F, Value, CharField, Case, When
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Concat
from django.template import Library
from django.urls import reverse
from cousinsmatter.utils import Paginator
from ..models import Photo

register = Library()


@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery, page_num, page_size):
  # include the previous and next photo urls in each photo
  photos = Photo.objects.filter(gallery=gallery).annotate(
    previous_url_short=Subquery(
      Photo.objects.filter(id__lt=OuterRef('id'))
      .filter(gallery=gallery)
      .order_by('-id')
      .values('image')[:1]
    ),
    previous_url=Case(
        When(previous_url_short__isnull=False, 
             then=Concat(Value(settings.MEDIA_URL), F('previous_url_short'), output_field=CharField())),
        default=Value(None)
    ),
    next_url_short=Subquery(
      Photo.objects.filter(id__gt=OuterRef('id'))
      .filter(gallery=gallery)
      .order_by('id')
      .values('image')[:1]
    ),
    next_url=Case(
        When(next_url_short__isnull=False, 
             then=Concat(Value(settings.MEDIA_URL), F('next_url_short'), output_field=CharField())),
        default=Value(None)
    ),
  )
  # print('query: ', photos.query)
  ptor = Paginator(photos, page_size, compute_link=lambda page: reverse('galleries:detail_page', args=[gallery.id, page]))
  page = ptor.get_page_data(page_num)
  return {"page": page}


@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False):
  return {
    "galleries": galleries if hasattr(galleries, '__iter__') else [galleries],
    "recursive": recursive,
  }
