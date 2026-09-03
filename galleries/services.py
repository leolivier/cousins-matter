import logging
import mimetypes
import os
import pathlib
import tempfile
import zipfile

from django.core.exceptions import SuspiciousFileOperation
from django.db import transaction
from django.db.models import Count, ObjectDoesNotExist, Prefetch
from django.forms import ValidationError
from django.utils.translation import gettext as _

from django_q.brokers import get_broker
from django_q.tasks import async_task

from .models import Gallery, Photo
from .tasks import ZipImport, handle_photo_file, post_create_photo

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# gallery detail / tree
# --------------------------------------------------------------------------------------


def get_gallery_detail_queryset():
  """
  Base queryset for the gallery detail view: owner/parent/cover selected, photo count
  annotated, and children prefetched with their cover. The view applies ``slug=`` (and
  raises 404) on top of this — fetching by slug is an HTTP/view concern.
  """
  return (
    Gallery.objects
    .select_related("owner", "parent", "cover")
    .annotate(photo_count=Count("photo"))
    .prefetch_related(Prefetch("children", queryset=Gallery.objects.select_related("cover")))
  )


def build_gallery_tree():
  """
  Builds the galleries tree for the tree view.

  Fetches all galleries in a single query (cover selected, photo count annotated) then
  assembles the parent→children relationships in Python onto each gallery's
  ``cached_children`` attribute, avoiding recursive N+1 queries. Returns the list of
  root galleries (each carrying its children on ``cached_children``); the view wraps
  it into the template context.
  """
  all_galleries = list(Gallery.objects.select_related("cover").annotate(photo_count=Count("photo")).order_by("name"))

  by_id = {g.pk: g for g in all_galleries}
  for g in all_galleries:
    g.cached_children = []
  roots = []
  for g in all_galleries:
    if g.parent_id and g.parent_id in by_id:
      by_id[g.parent_id].cached_children.append(g)
    elif not g.parent_id:
      roots.append(g)

  return roots


# --------------------------------------------------------------------------------------
# photo navigation
# --------------------------------------------------------------------------------------


def get_next_prev_photo(pk, side):
  """
  Returns the photo neighbouring ``pk`` in its gallery (ordered by id), wrapping around
  at the edges. ``side`` is ``"prev"``, ``"next"`` or ``None`` (returns ``pk``'s photo).
  Raises ``Photo.DoesNotExist`` if ``pk`` does not exist.
  """
  # this raises an exception Photo.DoesNotExist if the photo doesn't exist
  if side is None:
    return Photo.objects.get(pk=pk)

  gallery_id = Photo.objects.only("gallery_id").get(pk=pk).gallery_id
  photos = Photo.objects.filter(gallery=gallery_id).order_by("id")

  match side:
    case "prev":
      photo = photos.filter(id__lt=pk).last()
      if not photo:
        photo = photos.last()
    case "next":
      photo = photos.filter(id__gt=pk).first()
      if not photo:
        photo = photos.first()
    case _:
      raise ValueError("Invalid side: %s" % side)

  return photo or Photo.objects.get(id=pk)


# --------------------------------------------------------------------------------------
# bulk zip import
# --------------------------------------------------------------------------------------


def _get_parent_gallery(path: str, zimport: ZipImport):  # path should be directory
  """
  Returns the gallery inside which the gallery denoted by path is to be created.
  args: "path" should be one of a folder
  """
  parent_dir = os.path.dirname(os.path.normpath(path))
  return _get_or_create_gallery(parent_dir, zimport) if parent_dir != "" else zimport.root_gallery


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
  path = path.rstrip("/").removeprefix("./").replace("/./", "/")

  # check possible path traversal attempt (code from django internals)
  if ".." in pathlib.PurePath(path).parts:
    raise SuspiciousFileOperation(_("Detected path traversal attempt, '..' is not allowed in paths inside the zip file"))

  if path == ".":
    if zimport.root_gallery is None:
      raise ValidationError(_("Root gallery not found. Please select a root gallery. Create it first if necessary."))
    return zimport.root_gallery

  if path in zimport.galleries:  # gallery in cache
    return zimport.galleries[path]

  name = os.path.basename(os.path.normpath(path))
  description = _("Imported from zipfile directory %(path)s") % {"path": path}
  # Create the gallery and its not-yet-existing ancestors in a single transaction, so a
  # failure mid-chain never leaves a half-built gallery tree behind.
  with transaction.atomic():
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


def handle_zip(zip_file, task_group, owner_id, root_gallery=None):
  """
  reads a zip file and creates galleries for each folder
  and create tasks to create photos inside these galleries for each image in the folder.
  Galleries are named by the folder names and photos by the image file names.
  Files which are not photos are simply ignored.
  """
  if not zipfile.is_zipfile(zip_file):
    raise zipfile.BadZipFile(f"{zip_file} is not a zip file")

  tmpdir = tempfile.mkdtemp()
  zimport = ZipImport(owner_id=owner_id, root=tmpdir, group=task_group, root_gallery=root_gallery)
  zimport.register()
  broker = get_broker()
  # extract the zip file to a temporary directory
  with zipfile.ZipFile(zip_file, "r") as zip_ref:
    zip_ref.extractall(tmpdir)
  for dir, subdirs, files in os.walk(tmpdir):
    images = [file for file in files if mimetypes.guess_type(file)[0].startswith("image/")]
    if len(images) == 0:  # create galleries only if there are photos inside
      continue
    gallery_path = os.path.relpath(dir, tmpdir)  # get relative path from temp to see the galleries path
    gallery = _get_or_create_gallery(gallery_path, zimport)
    for image in images:
      async_task(
        handle_photo_file,
        zimport,
        dir,
        image,
        gallery.id,
        group=task_group,
        cached=False,
        hook=post_create_photo,
        broker=broker,
      )
      zimport.nbPhotos += 1
      logger.debug(f"created task for {image} group: {task_group}")

  return zimport
