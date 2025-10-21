import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.http import Http404, StreamingHttpResponse
from django.utils.translation import gettext as _
from django.views import generic
from wsgiref.util import FileWrapper


import os
import mimetypes
import tempfile
import zipfile

from cm_main.forms import PasswordResetForm
from cm_main.utils import get_media_storage

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
  # # Security: Make sure the path does not go back up the tree using '..'. Useless with any backend storage
  # if not os.path.normpath(the_file).startswith(os.path.normpath(settings.MEDIA_ROOT)):
  #   raise Http404(_("Path traversal detected"))

  media_storage = get_media_storage()
  if not media_storage.exists(media):
    raise Http404(_("Media not found"))
  chunk_size = 8192
  response = StreamingHttpResponse(
      FileWrapper(
          media_storage.open(media, "rb"),
          chunk_size,
      ),
      content_type=mimetypes.guess_type(media)[0],
  )
  response["Content-Length"] = media_storage.size(media)
  # response["Content-Disposition"] = f"inline; filename={filename}"
  response["Content-Disposition"] = "inline"
  return response


def send_zipfile(request):
  """
  Create a ZIP file on disk and transmit it in chunks of 8KB,
  without loading the whole file into memory. A similar approach can
  be used for large dynamic PDF files.
  """
  chunk_size = 8192
  temp = tempfile.TemporaryFile(suffix='.zip')
  archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
  files = []  # Select your files here.
  for filename in files:
      abs_filename = os.path.abspath(filename)
      rel_filename = filename if filename.startswith('./') else '.' / filename  # TODO: won't work on Windows
      archive.write(abs_filename, rel_filename)
  archive.close()
  response = StreamingHttpResponse(
    FileWrapper(
          open(temp, "rb"),
          chunk_size,
      ),
    content_type=mimetypes.guess_type(temp)[0],
  )
  response["Content-Type"] = 'application/zip'
  response["Content-Length"] = temp.tell()
  response["Content-Disposition"] = "attachment; filename=file.zip"
  temp.seek(0)
  return response
