import logging
import os
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import slugify
from django.urls import reverse
from cm_main.utils import check_file_size, create_thumbnail, protected_media_url

logger = logging.getLogger(__name__)


def get_path(instance, filename, subdir=None):
  """
  photos will be uploaded to MEDIA_ROOT/GALLERIES_DIR/<gallery_full_path>/<subdir>/<filename>.
  subdir is None or 'thumbnails' for thumbnails
  """
  if not instance.gallery_id:
    raise ValidationError(_("A photo must belong to a gallery."))
  path = os.path.join(settings.GALLERIES_DIR, instance.gallery.full_path(), subdir, filename) if subdir \
    else os.path.join(settings.GALLERIES_DIR, instance.gallery.full_path(), filename)
  logger.debug(f"photo is stored in {path}")
  return path


def photo_path(instance, filename):
  return get_path(instance, filename)


def thumbnail_path(instance, filename):
  return get_path(instance, filename, 'thumbnails')


def check_image_size(image):
  return check_file_size(image, settings.MAX_PHOTO_FILE_SIZE)


class Photo(models.Model):
  image = models.ImageField(_("Photo"), upload_to=photo_path, validators=[check_image_size],
                            height_field='image_height', width_field='image_width', max_length=1000, null=False)
  image_height = models.IntegerField(default=0)
  image_width = models.IntegerField(default=0)
  thumbnail = models.ImageField(upload_to=thumbnail_path, blank=True)
  name = models.CharField(_("Name"), max_length=70, blank=True)
  description = models.TextField(_("Description"), max_length=3000, blank=True)
  slug = models.SlugField(max_length=70, blank=True, null=False)
  date = models.DateField(_("Date"), help_text=_("Click on the month name or the year to change them quickly"))
  gallery = models.ForeignKey('Gallery', verbose_name="Gallery", on_delete=models.CASCADE, blank=True)
  uploaded_by = models.ForeignKey('members.Member', verbose_name=_("Uploaded by"), on_delete=models.CASCADE,
                                  blank=True, null=True)

  class Meta:
    ordering = ['id']
    indexes = [
      models.Index(fields=['gallery']),
      models.Index(fields=['name']),
      models.Index(fields=['gallery', 'id']),
    ]
    constraints = [
      models.UniqueConstraint(fields=('slug', 'gallery'), name="slugs must be unique inside their gallery"),
    ]

  def __str__(self):
    return f'{self.gallery.name}/{self.name}' if self.gallery_id else self.name

  def get_absolute_url(self):
    return reverse("galleries:photo", kwargs={"pk": self.pk})

  def clean(self):
    # should never happen except in tests
    if not self.gallery_id:
      raise ValidationError(_("A photo must belong to a gallery."))
    # name by default is the name of the file
    if not self.name:
      self.name = self.image.name.split('/')[-1]
    # compute slug
    self.slug = self.slug or slugify(self.name)

  def save(self, *args, **kwargs):

    self.full_clean()

    # need to save first to upload the image
    super().save(*args, **kwargs)

    try:
      self.thumbnail = create_thumbnail(self.image, settings.GALLERIES_THUMBNAIL_SIZE)
      super().save(force_update=True, update_fields=['thumbnail'])

    except Exception as e:
      # issue #120: if any exception during the thumbnail creation process, remove the photo from the database
      self.delete()
      raise ValidationError(f"Error during saving photo: {e}")

  def delete(self, *args, **kwargs):
      # delete the image and the thumbnail if they exist
      if self.image:
          self.image.delete(False)
      if self.thumbnail:
        self.thumbnail.delete(False)
      super().delete(*args, **kwargs)


class Gallery(models.Model):
  name = models.CharField(_("Name"), max_length=70)
  description = models.TextField(_("Description"), max_length=3000, blank=True)
  cover = models.ForeignKey('Photo', verbose_name=_("Cover Photo"), null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="cover_of"
                            )
  parent = models.ForeignKey('self', verbose_name=_("Parent gallery"), null=True, blank=True,
                             on_delete=models.CASCADE, related_name='children')
  slug = models.SlugField(max_length=70, blank=True, null=False)
  owner = models.ForeignKey('members.Member', verbose_name=_("Owner"), on_delete=models.CASCADE,
                            blank=True, null=True)

  class Meta:
    verbose_name_plural = _('galleries')

    ordering = ['name']
    indexes = [
      models.Index(fields=["parent", "name"]),
    ]
    constraints = [
      models.UniqueConstraint(fields=("slug", "parent"), name="slugs must be unique inside a parent gallery"),
    ]

  def __str__(self):
    return f'{self.parent}/{self.name}' if self.parent else self.name

  def get_absolute_url(self):
    return reverse("galleries:detail", kwargs={"pk": self.pk})

  def clean(self):
    # check parent_id != id
    if self.pk and self.parent_id == self.pk:
      raise ValidationError(_("A gallery can't be its own parent!"))
    # compute slug
    if not self.slug:
      slug = slugify(self.name)
      # the unique constraint on slug does not work if the parent is null
      # and it does not provide a friendly output if parent exists so check it manually
      if Gallery.objects.filter(slug=slug, parent=self.parent).exists():
        if self.parent:
          raise ValidationError(_("Another sub gallery of %(parent)s with the same name already exists") %
                                {'parent': self.parent.full_path()})
        else:
          raise ValidationError(_("Another root gallery with the same name already exists"))
      self.slug = slug

  def save(self, *args, **kwargs):
    self.full_clean()
    return super().save(*args, **kwargs)

  def full_path(self):
    return os.path.join(self.parent.full_path(), self.slug) if self.parent else self.slug

  def cover_url(self):
    return protected_media_url(self.cover.thumbnail.name) if self.cover else settings.DEFAULT_GALLERY_COVER_URL

  def rec_children_list(self):
    result = [self.pk]
    for child in self.children.all():
        result.extend(child.rec_children_list())
    return result
