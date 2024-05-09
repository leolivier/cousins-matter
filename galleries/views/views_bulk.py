import logging, zipfile, os, mimetypes, sys, tempfile, pathlib
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps
from datetime import datetime
from io import BytesIO
from django.forms import ValidationError
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _

from ..models import Gallery, Photo
from ..forms import BulkUploadPhotosForm

logger = logging.getLogger(__name__)

class BulkUploadPhotosView(LoginRequiredMixin, generic.FormView):
		template_name = "galleries/bulk_upload.html"
		form_class = BulkUploadPhotosForm
		success_url = reverse_lazy("galleries:galleries")
		galleries = {}
		nbPhotos = 0

		def _get_parent_gallery(self, path): # zipinfo should be directory
			"""
			Returns the gallery inside which the gallery denoted by path is to be created.
			args: "path" should be one of a folder
			"""
			parent_dir = os.path.dirname(os.path.normpath(path))
			return self._get_or_create_gallery(parent_dir) if parent_dir != '' else None

		def _get_photo_gallery(self, path):
			"""
			Returns the gallery in which the photo denoted by path is to be created.
			args: "path" should be one of an image
			"""
			dir = os.path.dirname(os.path.normpath(path))
			gallery = self._get_or_create_gallery(dir)
			if gallery is None:
				raise ValidationError(_("Photos can't be at the root of the zip file."))
			return gallery

		def _get_or_create_gallery(self, path: str): # zipinfo should be directory
			"""
			Creates a Gallery object based on the path. The path should denote a folder.
			If the path is made of several embedded folders, all Galleries are created 
			recursively and the parent relationship between galleries is built based on
			that. Paths are cleaned and checked before creating galleries.
			Throws SuspiciousFileOperation if a path traversal attempt is detected.
			If gallery with the same name and same parent already exists, it is simply 
			returned and not updated to avoid overwriting handwritten description
			"""
			# remove leading './', trailing slash and dots inside the path
			path = path.rstrip('/').removeprefix('./').replace('/./', '/')

			# check possible path traversal attempt (code from django internals)
			if ".." in pathlib.PurePath(path).parts:
				raise SuspiciousFileOperation(_("Detected path traversal attempt, '..' is not allowed in paths inside the zip file"))

			if path == '.': # should never happen
				return None

			if path in self.galleries:  # gallery in cache
				return self.galleries[path]
			
			name=os.path.basename(os.path.normpath(path))
			description = _(f'Imported from zipfile directory {path}')
			parent = self._get_parent_gallery(path)

			# Create gallery if it does not already exists.
	 		# Don't update it otherwise as we might overwrite handwritten description.
			gallery = Gallery.objects.filter(name=name, parent=parent)
			if not gallery.exists():
				gallery = Gallery.objects.create(name=name, parent=parent, description=description)
			else:
				gallery = gallery.first()
			# store gallery in the cache
			self.galleries[path] = gallery
			return gallery

		def _create_photo(self, zipinfo, filepath): # zipinfo should be an image
			"""
			creates a photo object based on the ZipInfo and the content of the 
			temporary file given by filepath.
			Photos are name by the file name. All folders in the path are transformed
			into embedded Galleries.
			Photos date is computed from the exif data of the image.
			WARNING: if an Photo with the same name already exist in the same gallery, we override it
			with the new image and date.
			"""
			# compute all needed fields
			filename = zipinfo.filename
			name=os.path.basename(os.path.normpath(filename))
			filename_wo_ext, ext = os.path.splitext(name)
			description = _(f'Imported from zipfile directory {filename}')
			gallery = self._get_photo_gallery(filename)

			# create photo using an in memory buffer (BytesIO)
			membuffer = BytesIO()
			with Image.open(filepath) as img:
				img = ImageOps.exif_transpose(img)	# avoid image rotating
				img.save(membuffer, format='JPEG', quality=90) # save the img in mem buffer
				exifdata = img.getexif() # get exif data for the image date
			
			# reset buffer to beginning
			membuffer.seek(0)
			size = sys.getsizeof(membuffer)
			
			# TODO: save all exif data as a json buffer? 
	 		# or extract them when showing image detail?
			
			# compute exif date
			DateTimeOriginal = 36867
			DateTime = 306
			date = exifdata.get(DateTimeOriginal) or exifdata.get(DateTime)
			date =  datetime.today() if date is None else \
				 			datetime.strptime(date, "%Y:%m:%d %H:%M:%S").date()
			# create image from in memory buffer
			image = InMemoryUploadedFile(membuffer, 'ImageField', f"{filename_wo_ext}.jpg", 
																					'image/jpeg', size, None)
			# create or update photo object in database
	 		# WARNING: if an image with the same name already exist in the galeery, we override it
			photo = Photo.objects.filter(name=name, gallery=gallery)
			if photo.exists():
				photo = photo.first()
				photo.image=image
				photo.date=date
				photo.save()
			else: 
				photo = Photo.objects.create(name=name, description=description, image=image, date=date, gallery=gallery)

			self.nbPhotos += 1
			return photo

		def _handle_zip(self, zip_file):
			"""
			reads a zip file and creates galleries for each folder 
			and photos inside these galleries for each image in the folder.
			Galleries are named by the folder names and photos by the image file names.
			Files which are not photos are simply ignored.
			"""

			if not zipfile.is_zipfile(zip_file):
				raise zipfile.BadZipFile(f"{zip_file} is not a zip file")
			
			with zipfile.ZipFile(zip_file, 'r') as zip_ref:
				# get a list of files/folders inside the zip with their info
				infos = zip_ref.infolist()

				for info in infos:
					path = info.filename
					if info.is_dir(): # gallery
						self._get_or_create_gallery(path)
					elif mimetypes.guess_type(path)[0].startswith('image/'): # photo
						# extract the file in a temporary folder and create a photo
						with tempfile.TemporaryDirectory() as temp:
							filepath = zip_ref.extract(info, path=temp)
							self._create_photo(info, filepath)
					else:
						pass # unknown file type, don't care
						
		def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
			form = BulkUploadPhotosForm(request.POST, request.FILES)
			if form.is_valid():
				try:
					self._handle_zip(request.FILES["zipfile"])
					messages.success(request, _(f"Zip file uploaded: {len(self.galleries)} galleries and {self.nbPhotos} photos created"))
				except Exception as e:
					messages.error(request, e.__str__())
					raise
			return super().post(request, *args, **kwargs)
