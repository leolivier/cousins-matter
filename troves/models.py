import logging
import os
import re
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from core.utils import create_thumbnail
from tenants.scoping import TenantModel

logger = logging.getLogger(__name__)


class Trove(TenantModel):
  CATEGORY_CHOICES = [
    ("history", _("History & Stories")),
    ("recipes", _("Recipes")),
    ("cousinades", _("Family meetings")),
    ("recollections", _("Recollections")),
    ("arts", _("Arts")),
    ("miscellaneous", _("Miscellaneous")),
  ]

  title = models.CharField(
    verbose_name=_("Title of the treasure (this will appear in the list)"),
    null=False,
    blank=False,
    max_length=110,
  )
  description = models.TextField(
    verbose_name=_("Description of the treasure (this will appear in the details)"),
    null=True,
    blank=True,
  )
  picture = models.ImageField(
    upload_to=settings.TROVE_PICTURE_DIRECTORY,
    verbose_name=_("Treasure photo"),
    null=False,
    blank=False,
  )
  thumbnail = models.ImageField(upload_to=settings.TROVE_THUMBNAIL_DIRECTORY, blank=True)
  file = models.FileField(
    upload_to=settings.TROVE_FILES_DIRECTORY,
    verbose_name=_("Treasure file"),
    blank=True,
    null=True,
  )
  url = models.URLField(
    verbose_name=_("External URL of the treasure (e.g. a YouTube video)"),
    blank=True,
    null=True,
    max_length=500,
  )
  category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  class Meta:
    verbose_name = _("trove")
    verbose_name_plural = _("troves")
    ordering = ["id"]
    indexes = [models.Index(fields=["tenant", "category"], name="troves_trov_tenant_c30fb4_idx")]

  def __str__(self):
    return self.title

  # Extracts the video id from watch, youtu.be and shorts URLs so a YouTube URL
  # can be canonicalized to its privacy-enhanced embed form. Any other https URL
  # is embedded as-is (CSP frame-src allows https:, see config/settings/base.py).
  _YOUTUBE_ID_RE = re.compile(
    r"^https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})(?:[?&].*)?$"
  )

  @property
  def embed_url(self):
    """URL to embed in an iframe, or None when the treasure must be a plain link.

    A YouTube URL (any site the user may have copied it from) is rewritten to the
    privacy-enhanced embed form; every other https URL is embedded as-is.
    http:// is not embeddable (mixed content is blocked on https pages).
    """
    if not self.url:
      return None
    if self.url.startswith("https://"):
      m = self._YOUTUBE_ID_RE.match(self.url)
      return f"https://www.youtube-nocookie.com/embed/{m.group(1)}?autoplay=0" if m else self.url
    return None

  @staticmethod
  def translate_category(category):
    return dict(Trove.CATEGORY_CHOICES)[category]

  def _thumbnail_path(self):
    base = self.picture.name.split("/")[-1]
    return os.path.join(settings.TROVE_THUMBNAIL_DIRECTORY, base)

  def clean(self):
    if self.owner is None:
      raise ValidationError(_("A treasure must have an owner."))

  def save(self, *args, **kwargs):
    self.ensure_tenant()  # before full_clean(): tenant is non-nullable
    self.full_clean()  # clean before save
    is_new = self.pk is None
    try:
      # the row and its thumbnail commit together or not at all
      with transaction.atomic():
        super().save(*args, **kwargs)
        self.thumbnail = create_thumbnail(self.picture, settings.TROVE_THUMBNAIL_SIZE)

        super().save(force_update=True, update_fields=["thumbnail"])

    except Exception as e:
      # issue #120: if any exception during the thumbnail creation process, the transaction rolls
      # the row back; on a new treasure, also drop the picture file left behind on storage
      if is_new and self.picture and default_storage.exists(self.picture.name):
        default_storage.delete(self.picture.name)
      raise ValidationError(f"Error during saving picture: {e}")

  def delete(self, *args, **kwargs):
    super().delete(*args, **kwargs)
    # remove the files only once the row deletion succeeded, so a failed delete never
    # leaves a row pointing at deleted files
    self.delete_picture()

  def delete_picture(self):
    default_storage.delete(self.picture.name)
    thumbnail_path = os.path.join(settings.TROVE_THUMBNAIL_DIRECTORY, self.picture.name.split("/")[-1])
    default_storage.delete(thumbnail_path)
    self.picture = None
