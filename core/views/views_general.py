from pathlib import Path
import logging
import mimetypes
from hashlib import blake2b
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import PasswordResetView as DefaultPasswordResetView
from django.core.files.storage import default_storage
from django.http import (
  Http404,
  HttpResponseNotModified,
  JsonResponse,
  StreamingHttpResponse,
)
from django.utils.translation import gettext as _
from django.views import generic
from django_q.tasks import async_task, result

from core.forms import PasswordResetForm
from core.mixins import LoginNotRequiredMixin
from core.services import health_check

logger = logging.getLogger(__name__)

# Media is private per user, so shared caches (Cloudflare, proxies) must not store it:
# "private" keeps them out and only the browser caches, which is per user by nature.
# Public media is anonymous and identical for everyone, so it can be cached at the edge.
PROTECTED_MEDIA_CACHE_CONTROL = "private, max-age=3600"
PUBLIC_MEDIA_CACHE_CONTROL = "public, max-age=86400"


class PasswordResetView(DefaultPasswordResetView):
  form_class = PasswordResetForm


class HomeView(LoginNotRequiredMixin, generic.TemplateView):
  template_name = "core/base.html"


def _download_media(
  request, media, cache_control: str = PROTECTED_MEDIA_CACHE_CONTROL
) -> StreamingHttpResponse | HttpResponseNotModified:
  """
  Internal helper function to download a media file.

  The file is streamed in chunks of 8KB to avoid loading the whole file into memory.
  :param request: The request object (unused)
  :param media: The name of the media file to download
  :param cache_control: The Cache-Control header value for the response
  :return: A StreamingHttpResponse object containing the media file
  :raises Http404: If the file is not found, or if the path is invalid
  """
  logger.debug(f"Downloading media {media}")

  hasher = blake2b()
  tbh = bytes(f"{request.user.username}@{media}", "utf-8")
  hasher.update(tbh)
  # RFC 7232 requires the ETag to be a quoted string; unquoted values are ignored
  # by some caches and intermediaries.
  media_etag = f'"{hasher.hexdigest()}"'
  request_etag = request.headers.get("If-None-Match", None)
  logger.debug(f"File modified: {media_etag != request_etag}")
  if request_etag and request_etag == media_etag:
    not_modified = HttpResponseNotModified()
    not_modified["ETag"] = media_etag
    not_modified["Cache-Control"] = cache_control
    return not_modified

  chunk_size = 64 * 1024
  try:
    media_file = default_storage.open(media, "rb")
    logger.debug(f"File size: {media_file.size}")
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
  response["Cache-Control"] = cache_control

  return response


def download_protected_media(request, media) -> StreamingHttpResponse | HttpResponseNotModified:
  """
  View to download a protected media file. Login required
  The file must be stored in the MEDIA_ROOT directory in the media backend storage as defined in the settings (e.g. S3).
  In multi-tenant mode, the first path segment must be the caller's tenant slug; platform superusers
  (request.tenant is None) stay unscoped.
  """
  if settings.MULTI_TENANT_ENABLED:
    tenant = getattr(request, "tenant", None)
    if tenant is not None and media.split("/", 1)[0] != tenant.slug:
      raise Http404(_("Media not found"))
  return _download_media(request, media)


@login_not_required
def download_public_media(request, media) -> StreamingHttpResponse | HttpResponseNotModified:
  """
  View to download a public media file. No login required
  The file must be stored in the PUBLIC_MEDIA_ROOT directory in the media backend storage as defined in the settings (e.g. S3).
  """
  return _download_media(request, Path("public") / media, cache_control=PUBLIC_MEDIA_CACHE_CONTROL)


@login_not_required
def health(request) -> JsonResponse:
  """
  Health check view.

  This view checks if the database connection and the redis connection are working.

  :return: A JsonResponse object containing a single key-value pair with the key 'status' and the value 'ok'
           if both connections are working, or 'db_error' if the database connection is not working , or
           'redis_error' if the redis connection is not working.
  :rtype: JsonResponse
  :status: 200 (OK) or 503 (Service Unavailable)
  """
  check: dict[str, str] = health_check()
  return JsonResponse(check, status=200 if check["status"] == "ok" else 503)


@login_not_required
def qhealth(request) -> JsonResponse:
  """
  Django Q Health check view.

  This view checks through Django Q if the database connection and the redis connection are working.

  :return: A JsonResponse object containing a single key-value pair with the key 'status' and the value 'ok'
           if both connections are working, or 'db_error' if the database connection is not working , or
           'redis_error' if the redis connection is not working.
  :rtype: JsonResponse
  :status: 200 (OK) or 503 (Service Unavailable)
  """
  task_id = async_task("core.services.health_check")
  check = result(task_id, 1000)
  status = 200 if check and "status" in check and check["status"] == "ok" else 503
  return JsonResponse(check, status=status, safe=False)
