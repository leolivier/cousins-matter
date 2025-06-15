import logging

from django.conf import settings
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
  the_file = settings.MEDIA_ROOT / media
  if not os.path.isfile(the_file):
    raise Http404(_("Media not found"))
  # filename = os.path.basename(the_file)
  chunk_size = 8192
  response = StreamingHttpResponse(
      FileWrapper(
          open(the_file, "rb"),
          chunk_size,
      ),
      content_type=mimetypes.guess_type(the_file)[0],

  )
  response["Content-Length"] = os.path.getsize(the_file)
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
