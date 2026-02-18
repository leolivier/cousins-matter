import logging
import shutil
import zipfile
import os
import mimetypes
import tempfile
import pathlib
import uuid

from django.core.exceptions import SuspiciousFileOperation
from django.db.models import ObjectDoesNotExist
from django.forms import ValidationError
from django_htmx.http import HttpResponseClientRefresh
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.utils.translation import gettext as _

from django_q.tasks import async_task, result_group, count_group
from django_q.brokers import get_broker

from ..models import Gallery
from ..forms import BulkUploadPhotosForm
from ..tasks import ZipImport, handle_photo_file, post_create_photo

logger = logging.getLogger(__name__)


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


class BulkUploadPhotosView(generic.FormView):
  template_name = "galleries/bulk_upload.html"
  form_class = BulkUploadPhotosForm
  success_url = reverse_lazy("galleries:galleries")

  def post(self, request, *args, **kwargs):
    # print("post bulk upload")
    form = BulkUploadPhotosForm(request.POST, request.FILES)
    if form.is_valid():
      try:
        zip_file = request.FILES["zipfile"]
        # task_group = request.POST.get("csrfmiddlewaretoken")  # not generated in test context
        task_group = uuid.uuid4().hex
        zimport = handle_zip(zip_file, task_group, request.user.id, form.cleaned_data.get("gallery"))
        hx_get_url = reverse("galleries:upload_progress", args=(task_group,))
        logger.debug(f"rendering first progress-bar url: {hx_get_url}")
        return render(
          request,
          "cm_main/common/progress-bar.html",
          {"hx_get": hx_get_url, "frequency": "1s", "value": 0, "max": zimport.nbPhotos, "text": "0%"},
          status=200,
        )
        # print("post upload progress returns", r.content)
        # return r
      except ValidationError as e:
        for err in e.messages:
          messages.error(request, err)
        return HttpResponseClientRefresh()
      except Exception as e:
        messages.error(request, e.__str__())
        return HttpResponseClientRefresh()
    else:
      for code, error in form.errors.items():
        messages.error(request, ": ".join(code, error))
      return HttpResponseClientRefresh()


def upload_progress(request, id):
  zimport = ZipImport.get(id)
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
  context = {
    "hx_get": request.get_full_path(),
    "frequency": "1s",
    "value": value,
    "max": max,
    "text": str(int(value * 100 / max)) + "%",
    "processed_objects": zimport.photos,
    "errors": zimport.errors,
  }
  if value == max:  # reached the end
    context["back_url"] = reverse("galleries:galleries")
    context["back_text"] = _("Back to galleries list")
    context["success"] = _("Zip file uploaded: %(lg)d galleries and %(nbp)d photos created") % {
      "lg": zimport.nbGalleries,
      "nbp": len(zimport.photos),
    }
    # clean temp directory
    shutil.rmtree(zimport.root)
    # remove zimport from the cache
    zimport.unregister()
    logger.debug(f"cleaned {zimport}")
  logger.debug(
    f"upload progress bar value: {value}, max: {max}, processed objects: {zimport.photos}, errors: {zimport.errors}"
  )
  return render(request, "cm_main/common/progress-bar.html", context)
