from django.template import Library
from django.urls import reverse
from cm_main.utils import Paginator, protected_media_url
from ..models import Photo

register = Library()


def get_gallery_photos(gallery):
  """
  Helper function returning all the photos in a gallery, including only the id, name, image and thumbnail fields.
  """
  return Photo.objects.filter(gallery=gallery).order_by("id").only("id", "name", "image", "thumbnail")


def complete_photos_data(page, page_num, num_pages):
  """
  Helper function returning all the photos of a page, adding the previous and next photo urls
  in each photo, and transforming URLs to protected media URLs
  """

  photos_dict = [{} for _ in range(len(page.object_list))]
  for idx, p in enumerate(page.object_list):
    pmu = protected_media_url(p.image.name)
    tmu = protected_media_url(p.thumbnail.name)

    photos_dict[idx] = {
      "id": p.id,
      "name": p.name,
      "image_url": pmu,
      "thumbnail_url": tmu,
    }
    if idx > 0:
      photos_dict[idx - 1]["next_url"] = pmu
      photos_dict[idx]["previous_url"] = photos_dict[idx - 1]["image_url"]

      if idx == len(page.object_list) - 1 and page_num != num_pages:
        # last photo of the page and not last page ==> take the next photo
        next_photo = Photo.objects.filter(gallery=p.gallery).order_by("id").filter(id__gt=p.id).first()
        photos_dict[idx]["next_url"] = protected_media_url(next_photo.image.name)

    else:  # first photo of the page
      if page_num > 1:  # not first page ==> take the previous photo
        prev_photo = Photo.objects.filter(gallery=p.gallery).order_by("-id").filter(id__lt=p.id).first()
        photos_dict[idx]["previous_url"] = protected_media_url(prev_photo.image.name)
      if len(page.object_list) == 1 and page_num != num_pages:  # only one photo per page and not last page
        next_photo = Photo.objects.filter(gallery=p.gallery).order_by("id").filter(id__gt=p.id).first()
        photos_dict[idx]["next_url"] = protected_media_url(next_photo.image.name)
  page.object_list = photos_dict


@register.inclusion_tag("galleries/photos_gallery.html")
def include_photos(gallery, page_num, page_size):
  photos = get_gallery_photos(gallery)
  ptor = Paginator(
    photos,
    page_size,
    compute_link=lambda page: reverse("galleries:detail_page", args=[gallery.id, page]),
  )
  if page_num > ptor.num_pages:
    page_num = ptor.num_pages
  page = ptor.get_page_data(page_num)
  complete_photos_data(page, page_num, ptor.num_pages)
  return {"page": page}


@register.inclusion_tag("galleries/galleries_list.html")
def include_galleries(galleries, recursive=False, level=0):
  return {
    "galleries": galleries if hasattr(galleries, "__iter__") else [galleries],
    "recursive": recursive,
    "level": level,
  }
