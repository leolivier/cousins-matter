import logging
import os
import sys

# import time
from dataclasses import dataclass, field
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps
from io import BytesIO
from django.forms import ValidationError
from django.utils.translation import gettext as _, gettext_lazy
from django_q.tasks import Task

from .models import Gallery, Photo

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

  @classmethod
  def get(cls, group: str):
    return ZIP_IMPORTS.get(group, None)


# in memory cache of ZipImports
ZIP_IMPORTS: dict[str, ZipImport] = {}


def create_photo(filename, filepath, zimport: ZipImport, gallery_id: str):
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
  filename_wo_ext, _ = os.path.splitext(filename)
  description = gettext_lazy("Imported from zipfile directory %(path)s") % {"path": filename}

  # create photo using an in memory buffer (BytesIO)
  membuffer = BytesIO()
  with Image.open(filepath) as img:
    img = ImageOps.exif_transpose(img)  # avoid image rotating
    img.save(membuffer, format="JPEG", quality=90)  # save the img in mem buffer
    exifdata = img.getexif()  # get exif data for the image date

  # reset buffer to beginning
  membuffer.seek(0)
  size = sys.getsizeof(membuffer)

  # TODO: save all exif data as a json buffer?
  # or extract them when showing image detail?

  # compute exif date
  DateTimeOriginalKey = 36867
  DateTimeKey = 306
  date = exifdata.get(DateTimeOriginalKey) or exifdata.get(DateTimeKey)
  date = datetime.today() if date is None or date.startswith("0000") else datetime.strptime(date, "%Y:%m:%d %H:%M:%S").date()
  # create image from in memory buffer
  image = InMemoryUploadedFile(membuffer, "ImageField", f"{filename_wo_ext}.jpg", "image/jpeg", size, None)
  # create or update photo object in database
  # WARNING: if an image with the same name already exist in the gallery, we override it
  photo = Photo.objects.filter(name=filename, gallery__id=gallery_id)
  if photo.exists():
    photo = photo.first()
    photo.image = image
    photo.date = date
    photo.save()
  else:
    photo = Photo.objects.create(
      name=filename, description=description, image=image, date=date, gallery_id=gallery_id, uploaded_by_id=zimport.owner_id
    )

  return os.path.relpath(filepath, zimport.root)


def handle_photo_file(zimport: ZipImport, dir: str, image: str, gallery_id: str):
  errors = []
  filepath = os.path.join(dir, image)
  photo_path = None
  try:
    # time.sleep(4)  # artificially slow down fo testing
    photo_path = create_photo(image, filepath, zimport, gallery_id)
  except OSError as oserror:
    # print an error but continue with next photo
    error_msg = _("Unable to import photo '%(path)s', it was ignored") % {"path": os.path.relpath(filepath, zimport.root)}
    errors.append(f"""{error_msg}: {oserror.strerror}""")
    logger.exception(f"Error while importing photo {filepath}", exc_info=True)
  except ValidationError as verr:
    errors.extend(verr.messages)
    logger.exception(f"Error while importing photo {filepath}", exc_info=True)
  except Exception as e:
    errors.append(str(e))
    logger.exception(f"Error while importing photo {filepath}", exc_info=True)

  return photo_path, errors


def post_create_photo(task: Task):
  logger.info(f"create photo {task.args} status: {task.success} result: {task.result} group: {task.group}")
