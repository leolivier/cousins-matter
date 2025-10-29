import logging
import os
import sys
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from io import BytesIO
from PIL import Image, ImageOps, ImageFile

logger = logging.getLogger(__name__)
# issue #120 try to avoid error about truncated images when creating thumbnails
ImageFile.LOAD_TRUNCATED_IMAGES = True


class Trove(models.Model):
  CATEGORY_CHOICES = [
      ('history', _('History & Stories')),
      ('recipes', _('Recipes')),
      ('cousinades', _('Family meetings')),
      ('recollections', _('Recollections')),
      ('arts', _('Arts')),
      ('miscellaneous', _('Miscellaneous')),
  ]

  title = models.CharField(verbose_name="Title of the treasure (this will appear in the list)",
                           null=False, blank=False, max_length=110)
  description = models.TextField(verbose_name=_("Description of the treasure (this will appear in the details)"),
                                 null=True, blank=True)
  picture = models.ImageField(upload_to=settings.TROVE_PICTURE_DIRECTORY, verbose_name=_("Treasure photo"),
                              null=False, blank=False)
  thumbnail = models.ImageField(upload_to=settings.TROVE_THUMBNAIL_DIRECTORY, blank=True)
  file = models.FileField(upload_to=settings.TROVE_FILES_DIRECTORY, verbose_name=_("Treasure file"),
                          blank=True, null=True)
  category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  class Meta:
    verbose_name = _('trove')
    verbose_name_plural = _('troves')
    ordering = ['id']
    indexes = [
      models.Index(fields=["category"]),
    ]

  def __str__(self):
      return self.title

  @staticmethod
  def translate_category(category):
    return dict(Trove.CATEGORY_CHOICES)[category]

  def _thumbnail_path(self):
    return os.path.join(settings.TROVE_THUMBNAIL_DIRECTORY, os.path.basename(self.picture.path))

  def clean(self):
    if self.owner is None:
      raise ValidationError(_("A treasure must have an owner."))

  def save(self, *args, **kwargs):
    self.full_clean()  # clean before save
    super().save(*args, **kwargs)
    try:
      # create thumbnail
      tns = settings.TROVE_THUMBNAIL_SIZE
      output_thumb = BytesIO()
      filename = os.path.basename(self.picture.path)
      file, ext = os.path.splitext(filename)
      with Image.open(self.picture.path) as img:
        if img.height > tns or img.width > tns:
          size = tns, tns
          img.thumbnail(size)
          img = ImageOps.exif_transpose(img)  # avoid image rotating
          img.save(output_thumb, format='JPEG', quality=90)
          size = sys.getsizeof(output_thumb)
          self.thumbnail = InMemoryUploadedFile(output_thumb, 'ImageField', f"{file}.jpg",
                                                'image/jpeg', size, None)
          logger.debug(f"Resized and saved thumbnail for {self.picture.path} to {self.thumbnail.path}, size={size}")
        else:  # small photos are used directly as thumbnails
          self.thumbnail = self.picture

      super().save(force_update=True, update_fields=['thumbnail'])

    except Exception as e:
      # issue #120: if any exception during the thumbnail creation process, remove the photo from the database
      self.delete()
      raise ValidationError(f"Error during saving picture: {e}")

  def delete(self, *args, **kwargs):
    self.delete_picture()
    super().delete(*args, **kwargs)

  def delete_picture(self):
    default_storage.delete(self.picture.path)
    thumbnail_path = os.path.join(settings.TROVE_THUMBNAIL_DIRECTORY, os.path.basename(self.picture.path))
    default_storage.delete(thumbnail_path)
    self.picture = None
