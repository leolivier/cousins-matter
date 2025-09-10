import logging
import shutil
# import time
import zipfile
import os
import mimetypes
import sys
import tempfile
import pathlib
from dataclasses import dataclass, field
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps
from io import BytesIO
from django.db.models import ObjectDoesNotExist
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django_q.tasks import async_task, result_group, Task, count_group

from cm_main.utils import ajax_redirect

from ..models import Gallery, Photo
from ..forms import BulkUploadPhotosForm

logger = logging.getLogger(__name__)


@dataclass
class ZipImport:
    root: str = ""  # temp directory where the zip is extracted
    owner_id: str = ""  # member id of the member who imports the photos
    galleries: dict[Gallery] = field(default_factory=dict)  # galleries cache, contains both created and pre-existing galleries
    nbPhotos: int = 0  # number of tasks created for importing photos
    nbGalleries: int = 0
    group: str = ""  # group of tasks
    # photos and errors are sets to avoid duplicates, they are filled in upload_progress (so, after tasks are finished)
    photos: set[str] = field(default_factory=set)
    errors: set[str] = field(default_factory=set)

    def register(self):
      ZIP_IMPORTS[self.group] = self

    def unregister(self):
      if self.group in ZIP_IMPORTS:
        del ZIP_IMPORTS[self.group]


# in memory cache of ZipImports
ZIP_IMPORTS: dict[ZipImport] = {}


def _get_parent_gallery(path: str, zimport: ZipImport):  # path should be directory
    """
    Returns the gallery inside which the gallery denoted by path is to be created.
    args: "path" should be one of a folder
    """
    parent_dir = os.path.dirname(os.path.normpath(path))
    return _get_or_create_gallery(parent_dir, zimport) if parent_dir != '' else None


def _get_or_create_gallery(path: str, zimport: ZipImport):
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

  if path == '.':  # should never happen
    return None

  if path in zimport.galleries:  # gallery in cache
    return zimport.galleries[path]

  name = os.path.basename(os.path.normpath(path))
  description = _('Imported from zipfile directory %(path)s') % {'path': path}
  parent = _get_parent_gallery(path, zimport)

  # Create gallery if it does not already exists.
  # Don't update it otherwise as we might overwrite handwritten description.
  try:
    gallery = Gallery.objects.get(name=name, parent=parent)
  except ObjectDoesNotExist:
    gallery = Gallery.objects.create(name=name, parent=parent, description=description, owner_id=zimport.owner_id)
    zimport.nbGalleries += 1
  # store gallery in the cache
  zimport.galleries[path] = gallery
  return gallery


def _create_photo(filename, filepath, zimport: ZipImport, gallery_id: str):
  """
  creates a photo object based on the filename and the content of the
  temporary file given by filepath (so filename should describe an image)
  Photos are named by the file name. All folders in the path are transformed
  into embedded Galleries.
  Photos date is computed from the exif data of the image.
  WARNING: if a Photo with the same name already exist in the same gallery, we override it
  with the new image and date.
  """
  # compute all needed fields
  filename_wo_ext, ext = os.path.splitext(filename)
  description = _('Imported from zipfile directory %(path)s') % {'path': filename}

  # create photo using an in memory buffer (BytesIO)
  membuffer = BytesIO()
  with Image.open(filepath) as img:
    img = ImageOps.exif_transpose(img)  # avoid image rotating
    img.save(membuffer, format='JPEG', quality=90)  # save the img in mem buffer
    exifdata = img.getexif()  # get exif data for the image date

  # reset buffer to beginning
  membuffer.seek(0)
  size = sys.getsizeof(membuffer)

  # TODO: save all exif data as a json buffer?
  # or extract them when showing image detail?

  # compute exif date
  DateTimeOriginal = 36867
  DateTime = 306
  date = exifdata.get(DateTimeOriginal) or exifdata.get(DateTime)
  date = datetime.today() if date is None or date.startswith("0000") else \
    datetime.strptime(date, "%Y:%m:%d %H:%M:%S").date()
  # create image from in memory buffer
  image = InMemoryUploadedFile(membuffer, 'ImageField', f"{filename_wo_ext}.jpg",
                               'image/jpeg', size, None)
  # create or update photo object in database
  # WARNING: if an image with the same name already exist in the gallery, we override it
  photo = Photo.objects.filter(name=filename, gallery__id=gallery_id)
  if photo.exists():
    photo = photo.first()
    photo.image = image
    photo.date = date
    photo.save()
  else:
    photo = Photo.objects.create(name=filename, description=description, image=image, date=date,
                                 gallery_id=gallery_id, uploaded_by_id=zimport.owner_id)

  return os.path.relpath(filepath, zimport.root)


def _handle_photo_file(zimport: ZipImport, dir: str, image: str, gallery_id: str):
  errors = []
  filepath = os.path.join(dir, image)
  photo_path = None
  try:
    # time.sleep(4)  # artificially slow down fo testing
    photo_path = _create_photo(image, filepath, zimport, gallery_id)
  except OSError as oserror:
    # print an error but continue with next photo
    error_msg = _("Unable to import photo '%(path)s', it was ignored") % {
                  'path': os.path.relpath(filepath, zimport.root)
                  }
    errors.append(f'''{error_msg}: {oserror.strerror}''')
  except ValidationError as verr:
    errors.extend(verr.messages)

  return photo_path, errors


def _post_create_photo(task: Task):
  logger.info(f"create photo {task.args} status: {task.success} result: {task.result} group: {task.group}")


def _handle_zip(zip_file, task_group, owner_id):
  """
  reads a zip file and creates galleries for each folder
  and create tasks to create photos inside these galleries for each image in the folder.
  Galleries are named by the folder names and photos by the image file names.
  Files which are not photos are simply ignored.
  """
  if not zipfile.is_zipfile(zip_file):
    raise zipfile.BadZipFile(f"{zip_file} is not a zip file")

  tmpdir = tempfile.mkdtemp()
  zimport = ZipImport(owner_id=owner_id, root=tmpdir, group=task_group)
  zimport.register()
  # extract the zip file to a temporary directory
  with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(tmpdir)
  for dir, subdirs, files in os.walk(tmpdir):
    images = [file for file in files if mimetypes.guess_type(file)[0].startswith('image/')]
    if len(images) == 0:  # create galleries only if there are photos inside
      continue
    gallery_path = os.path.relpath(dir, tmpdir)  # get relative path from temp to see the galleries path
    gallery = _get_or_create_gallery(gallery_path, zimport)
    for image in images:
      async_task(_handle_photo_file, zimport, dir, image, gallery.id,
                 group=task_group, cached=False, hook=_post_create_photo)
      zimport.nbPhotos += 1
      logger.debug(f"created task for {image} group: {task_group}")

  return zimport


class BulkUploadPhotosView(LoginRequiredMixin, generic.FormView):
    template_name = "galleries/bulk_upload.html"
    form_class = BulkUploadPhotosForm
    success_url = reverse_lazy("galleries:galleries")

    def post(self, request, *args, **kwargs):
      # print("post bulk upload")
      form = BulkUploadPhotosForm(request.POST, request.FILES)
      if form.is_valid():
        try:
          zip_file = request.FILES["zipfile"]
          task_group = request.POST.get("csrfmiddlewaretoken")
          zimport = _handle_zip(zip_file, task_group, request.user.id)
          hx_get_url = reverse("galleries:upload_progress", args=(task_group,))
          logger.debug(f"rendering first progress-bar url: {hx_get_url}")
          return render(request, "cm_main/common/progress-bar.html",
                        {"hx_get": hx_get_url, "frequency": "1s",
                         "value": 0, "max": zimport.nbPhotos, "text": "0%"},
                        status=200)
          # print("post upload progress returns", r.content)
          # return r
        except ValidationError as e:
          for err in e.messages:
            messages.error(request, err)
          return ajax_redirect(request, reverse("galleries:bulk_upload"))
        except Exception as e:
          messages.error(request, e.__str__())
          return ajax_redirect(request, reverse("galleries:bulk_upload"))
      else:
        for code, error in form.errors.items():
          messages.error(request, ": ".join(code, error))
        return ajax_redirect(request, reverse("galleries:bulk_upload"))


@login_required
def upload_progress(request, id):
  zimport = ZIP_IMPORTS.get(id, None)
  logger.debug(f"upload progress group: {id}, zimport: {zimport}")
  if not zimport:  # removed from the list when completed
    raise Http404(_("Upload not found"))
  value = count_group(id)
  max = zimport.nbPhotos

  # get already finished tasks
  results = result_group(id, failures=True, count=value, cached=False)
  # print error messages first then successful import
  if results:
    for photo_path, errors in results:
      if photo_path:
        zimport.photos.add(photo_path)
      if errors:
        for err in errors:
          zimport.errors.add(err)
  context = {"hx_get": request.get_full_path(), "frequency": "1s",
             "value": value, "max": max, "text": str(int(value*100/max)) + "%",
             "processed_objects": zimport.photos, "errors": zimport.errors}
  if value == max:  # reached the end
    context["back_url"] = reverse('galleries:galleries')
    context["back_text"] = _('Back to galleries list')
    context["success"] = _("Zip file uploaded: %(lg)d galleries and %(nbp)d photos created") % {
                          'lg': zimport.nbGalleries, 'nbp': len(zimport.photos)
                          }
    # clean temp directory
    shutil.rmtree(zimport.root)
    # remove zimport from the cache
    zimport.unregister()
    logger.debug(f"cleaned {zimport}")
  logger.debug(f"upload progress bar value: {value}, max: {max}, "
               f"processed objects: {zimport.photos}, errors: {zimport.errors}")
  return render(request, "cm_main/common/progress-bar.html", context)
