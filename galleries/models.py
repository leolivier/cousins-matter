from typing import Iterable
from django.db import models
from PIL import Image, ImageOps
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from cousinsmatter import settings
from django.template.defaultfilters import slugify
import logging, os, sys
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse

logger = logging.getLogger(__name__)

def get_path(instance, filename, subdir=None):
	"""
	photos will be uploaded to MEDIA_ROOT/GALLERIES_DIR/<gallery_full_path>/<subdir>/<filename>.
	subdir is None or 'thumbnails' for thumbnails
	"""
	dir = os.path.join(settings.GALLERIES_DIR, instance.gallery.full_path())
	if subdir: dir = os.path.join(dir, subdir)
	os.makedirs(dir, exist_ok=True)
	path = os.path.join(dir, filename)
	logger.info(f"photo is stored in {path}")
	return path

def photo_path(instance, filename):
	return get_path(instance, filename)

def thumbnail_path(instance, filename):
	return get_path(instance, filename, 'thumbnails')

def get_default_cover():
	"""
	return the default cover used in the galleries as long as 
	the user didn't define it
	"""
	cover = Photo.objects.filter(gallery__isnull=True)
	if cover.exists(): 
		return cover.first()
	else:
		default_cover_file = os.path.join(settings.MEDIA_URL, "galleries/default_gallery_cover.jpg")
		membuf = BytesIO()
		with Image.open(default_cover_file) as img:
			img = ImageOps.exif_transpose(img)	# avoid image rotating
			img.save(membuf, format='JPEG', quality=90)
			size = sys.getsizeof(membuf)
			default_cover_image = InMemoryUploadedFile(membuf, 'ImageField', os.path.basename(default_cover_file), 
																					'image/jpeg', size, None)
			cover = Photo.objects.create(image=default_cover_image, gallery=None)
			return cover

class Photo(models.Model):
	image = models.ImageField(_("Photo"), upload_to=photo_path)
	thumbnail = models.ImageField(upload_to=thumbnail_path, blank=True)
	name = models.CharField(_("Name"), max_length=70, blank=True)
	description = models.TextField(_("Description"), max_length=300, blank=True) # TODO: rich editor
	slug = models.SlugField(max_length=70, blank=True, null=False)
	date = models.DateField(_("Date"))
	gallery = models.ForeignKey('Gallery', verbose_name="Gallery", on_delete=models.CASCADE, blank=True)

	class Meta:
		ordering = ['gallery', 'date', 'name']
		indexes = [
			models.Index(fields=["gallery", "date", "name"]),
		]
		constraints = [
			models.UniqueConstraint(fields=("slug", "gallery"), name="slugs must be unique inside their gallery"),
		]

	def __str__(self):
		return f'{self.gallery.name}/{self.name}'

	def get_absolute_url(self):
		return reverse("galleries:photo", kwargs={"pk": self.pk})

	def clean(self):
		# name by default is the name of the file
		self.name =	self.name or os.path.basename(self.image.path)
		# compute slug
		self.slug =	self.slug or slugify(self.name)

	def save(self, *args, **kwargs):

		self.full_clean()

		# need to save first to uplad the image
		super().save(*args, **kwargs)

		# create thumbnail
		tns = settings.GALLERIES_THUMBNAIL_SIZE
		output_thumb = BytesIO()
		filename = os.path.basename(self.image.path)
		file, ext = os.path.splitext(filename)
		with Image.open(self.image.path) as img:
			if img.height > tns or img.width > tns:
				size = tns, tns
				img.thumbnail(size)
				img = ImageOps.exif_transpose(img)	# avoid image rotating
				img.save(output_thumb, format='JPEG', quality=90)
				size = sys.getsizeof(output_thumb)
				self.thumbnail = InMemoryUploadedFile(output_thumb, 'ImageField', f"{file}.jpg", 
																						'image/jpeg', size, None)
				logger.info(f"Resized and saved thumbnail for {self.image.path} to {self.thumbnail.path}, size={size}")
			else: # small photos are used directly as thumbnails
				self.thumbnail = self.image

		super().save(force_update=True)


class Gallery(models.Model):
	name = models.CharField(_("Name"), max_length=70)
	description = models.TextField(_("Description"), max_length=300, blank=True)
	cover = models.ForeignKey('Photo', verbose_name=_("Cover Photo"), null=True, blank=True, 
													 on_delete=models.DO_NOTHING, related_name="cover_of"
													 )
	parent = models.ForeignKey('self', verbose_name=_("Parent gallery"), null=True, blank=True, 
														on_delete=models.CASCADE, related_name='children') 
	slug = models.SlugField(max_length=70, blank=True, null=False)

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
		if self.parent:
			return f'{self.parent}/{self.name}'

	def get_absolute_url(self):
		return reverse("galleries:display", kwargs={"pk": self.pk})
	
	def clean(self):
		# compute slug
		self.slug = self.slug or slugify(self.name)
		if not self.cover_id:
			photos = Photo.objects.filter(gallery=self)
			self.cover = photos.first() if photos.exists() else get_default_cover()

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)
	
	def full_path(self):
		if not self.parent: return self.slug
		return os.path.join(self.parent.full_path(), self.slug)

	def cover_url(self):
		return self.cover.thumbnail.url if self.cover else os.path.join('/', settings.STATIC_URL, 'galleries/default-gallery-cover.jpg')

