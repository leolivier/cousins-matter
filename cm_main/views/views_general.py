import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.core.files.storage import default_storage
from django.db import connections, DatabaseError
from django.http import (
  Http404,
  StreamingHttpResponse,
  HttpResponseNotModified,
  JsonResponse,
)
from django.utils.translation import gettext as _
from django.views import generic
from django_q.tasks import async_task, result
from wsgiref.util import FileWrapper

from hashlib import blake2b
import os
import mimetypes
import redis
import tempfile
import zipfile

from cm_main.forms import PasswordResetForm

logger = logging.getLogger(__name__)


class PasswordResetView(PasswordResetView):
  form_class = PasswordResetForm


class OnlyAdminMixin(LoginRequiredMixin, PermissionRequiredMixin):
  raise_exception = True
  permission_required = "is_superuser"


class HomeView(generic.TemplateView):
  template_name = "cm_main/base.html"


@login_required
def download_protected_media(request, media):
  """
  View to download a protected media file.

  The file is streamed in chunks of 8KB to avoid loading the whole file into memory.
  The file must be stored in the MEDIA_ROOT directory in the media backend storage as defined in the settings (e.g. S3).
  :param request: The request object (unused)
  :param media: The name of the media file to download
  :return: A StreamingHttpResponse object containing the media file
  :raises Http404: If the file is not found, or if the path is invalid
  """
  logger.debug(f"Downloading protected media {media}")

  hasher = blake2b()
  tbh = bytes(f"{request.user.username}@{media}", "utf-8")
  hasher.update(tbh)
  media_etag = hasher.hexdigest()

  request_etag = request.headers.get("If-None-Match", None)
  if request_etag and request_etag == media_etag:
    return HttpResponseNotModified()

  chunk_size = 64 * 1024
  try:
    media_file = default_storage.open(media, "rb")
    response = StreamingHttpResponse(
      FileWrapper(media_file, chunk_size),
      content_type=mimetypes.guess_type(media)[0],
    )
  except FileNotFoundError:
    raise Http404(_("Media not found"))
  except Exception as e:
    raise Http404(_("Error when retrieving media: %s") % e)

  response["Content-Length"] = media_file.size
  # response["Content-Disposition"] = f"inline; filename={filename}"
  response["Content-Disposition"] = "inline"
  response["ETag"] = media_etag

  return response


def health_check():
  try:
    with connections["default"].cursor() as cursor:
      cursor.execute("SELECT 1")
      cursor.fetchone()
  except DatabaseError as e:
    return {"status": "db_error", "msg": str(e)}
  try:
    r = redis.Redis(
      host=os.getenv("REDIS_HOST", "redis"),
      port=os.getenv("REDIS_PORT", 6379),
      decode_responses=True,
    )
    r.ping()
  except redis.exceptions.ConnectionError as e:
    return {"status": "redis_error", "msg": str(e)}
  return {"status": "ok"}


def health(request):
  """
  Health check view.

  This view checks if the database connection and the redis connection are working.

  :return: A JsonResponse object containing a single key-value pair with the key 'status' and the value 'ok'
           if both connections are working, or 'db_error' if the database connection is not working , or
           'redis_error' if the redis connection is not working.
  :rtype: JsonResponse
  :status: 200 (OK) or 503 (Service Unavailable)
  """
  check = health_check()
  return JsonResponse(check, status=200 if check["status"] == "ok" else 503)


def qhealth(request):
  """
  Django Q Health check view.

  This view checks through Django Q if the database connection and the redis connection are working.

  :return: A JsonResponse object containing a single key-value pair with the key 'status' and the value 'ok'
           if both connections are working, or 'db_error' if the database connection is not working , or
           'redis_error' if the redis connection is not working.
  :rtype: JsonResponse
  :status: 200 (OK) or 503 (Service Unavailable)
  """
  task_id = async_task("cm_main.views.views_general.health_check")
  check = result(task_id, 1000)
  status=200 if check and "status" in check and check["status"] == "ok" else 503
  return JsonResponse(check, status=status)


def send_zipfile(request):
  """
  Create a ZIP file on disk and transmit it in chunks of 8KB,
  without loading the whole file into memory. A similar approach can
  be used for large dynamic PDF files.
  """
  chunk_size = 8192
  temp = tempfile.TemporaryFile(suffix=".zip")
  archive = zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED)
  files = []  # Select your files here.
  for filename in files:
    abs_filename = os.path.abspath(filename)
    rel_filename = filename if filename.startswith("./") else "." / filename  # TODO: won't work on Windows
    archive.write(abs_filename, rel_filename)
  archive.close()
  response = StreamingHttpResponse(
    FileWrapper(
      open(temp, "rb"),
      chunk_size,
    ),
    content_type=mimetypes.guess_type(temp)[0],
  )
  response["Content-Type"] = "application/zip"
  response["Content-Length"] = temp.tell()
  response["Content-Disposition"] = "attachment; filename=file.zip"
  temp.seek(0)
  return response
