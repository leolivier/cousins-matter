# import json
import os
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from cm_main.utils import create_thumbnail
from members.models import Member


class Categories:
    from .categories import CATEGORIES

    cat_list = None
    cat_keys = None

    @staticmethod
    def get_category(category):
        return Categories.CATEGORIES[category]

    @staticmethod
    def list_categories() -> list[tuple[str, str]]:
        if Categories.cat_list is None:
            Categories.cat_list = [
                (c, v["translation"]) for c, v in Categories.CATEGORIES.items()
            ]
        return Categories.cat_list

    @staticmethod
    def list_category_keys() -> list[str]:
        if Categories.cat_keys is None:
            Categories.cat_keys = Categories.CATEGORIES.keys()
        return Categories.cat_keys

    @staticmethod
    def list_subcategories(category) -> list[tuple[str, str]]:
        return [
            (k, v) for k, v in Categories.CATEGORIES[category]["subcategories"].items()
        ]

    @staticmethod
    def display_category(category) -> str:
        return Categories.CATEGORIES[category]["translation"]

    @staticmethod
    def display_subcategory(category, subcategory) -> str:
        return Categories.CATEGORIES[category]["subcategories"][subcategory]

    def __call__(self, *args, **kwds):
        return Categories.CATEGORIES


class ClassifiedAd(models.Model):
    ITEM_STATUS_TYPES = (
        ("new", _("New")),
        ("like_new", _("Like New")),
        ("very_good", _("Very Good")),
        ("good", _("Good")),
        ("fair", _("Fair")),
        ("poor", _("Poor")),
        ("parts", _("For Parts/Not Working")),
    )
    AD_STATUS_FOR_SALE = "for_sale"
    AD_STATUS_SOLD = "sold"
    AD_STATUS_CLOSED = "closed"
    AD_STATUSES = (
        (AD_STATUS_FOR_SALE, _("For Sale")),
        (AD_STATUS_SOLD, _("Sold")),
        (AD_STATUS_CLOSED, _("Closed")),
    )
    SHIPPING_METHODS = (
        ("pickup", _("Pickup only")),
        ("shipping", _("Shipping only")),
        ("both", _("Pickup or Shipping")),
    )

    title = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=55)
    subcategory = models.CharField(max_length=255)
    description = models.TextField()
    shipping_method = models.CharField(
        max_length=255, choices=SHIPPING_METHODS, default="pickup"
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=25)
    item_status = models.CharField(
        max_length=255, choices=ITEM_STATUS_TYPES, default="new"
    )
    ad_status = models.CharField(
        max_length=255, choices=AD_STATUSES, default="for_sale"
    )
    owner = models.ForeignKey(Member, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_created"]
        verbose_name = _("Classified Ad")
        verbose_name_plural = _("Classified Ads")
        indexes = [
            models.Index(fields=["owner", "category", "subcategory"]),
        ]

  def __str__(self) -> str:
    return self.title

  def display_category(self) -> str:
    return Categories.display_category(self.category)

    def display_subcategory(self) -> str:
        if self.subcategory:
            return Categories.display_subcategory(self.category, self.subcategory)
        return "-"

  def display_shipping_method(self) -> str:
    return dict(self.SHIPPING_METHODS).get(self.shipping_method)

  def display_item_status(self) -> str:
    return dict(self.ITEM_STATUS_TYPES).get(self.item_status)

  def display_ad_status(self) -> str:
    return dict(self.AD_STATUSES).get(self.ad_status)


def get_photo_path(photo, filename):
    """
    photos will be uploaded to MEDIA_ROOT/classified_ads/<ad_id>/<filename>.
    """
    return os.path.join("classified_ads", str(photo.ad.id), filename)


def get_thumbnail_path(photo, filename):
    return get_photo_path(photo, os.path.join("thumbnails", filename))


class AdPhoto(models.Model):
    image = models.ImageField(upload_to=get_photo_path)
    thumbnail = models.ImageField(upload_to=get_thumbnail_path, blank=True)

    ad = models.ForeignKey(
        ClassifiedAd, related_name="photos", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Ad Photo")
        verbose_name_plural = _("Ad Photos")
        indexes = [
            models.Index(fields=["ad"]),
        ]

    def save(self, *args, **kwargs):
        # need to save first to upload the image
        super().save(*args, **kwargs)
        try:
            self.thumbnail = create_thumbnail(
                self.image, settings.GALLERIES_THUMBNAIL_SIZE
            )
            super().save(force_update=True, update_fields=["thumbnail"])
        except Exception as e:
            # issue #120: if any exception during the thumbnail creation process, remove the photo from the database
            self.delete()
            raise ValidationError(f"Error during saving photo: {e}")

    def delete(self, *args, **kwargs):
        # delete the image and the thumbnail if they exist
        if self.thumbnail and self.thumbnail != self.image:
            self.thumbnail.delete(False)
        if self.image:
            self.image.delete(False)
        super().delete(*args, **kwargs)
