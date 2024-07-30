import logging
import os
import mimetypes
import tempfile
import zipfile
import requests

from django.shortcuts import render
from django.views import generic
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, Http404
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model, get_user
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.template.loader import render_to_string
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from wsgiref.util import FileWrapper

from chat.models import ChatMessage, ChatRoom
from forum.models import Comment, Message, Post
from galleries.models import Gallery, Photo
from members.models import Member

from .forms import ContactForm

logger = logging.getLogger(__name__)


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
  filename = os.path.basename(the_file)
  chunk_size = 8192
  response = StreamingHttpResponse(
      FileWrapper(
          open(the_file, "rb"),
          chunk_size,
      ),
      content_type=mimetypes.guess_type(the_file)[0],
  )
  response["Content-Length"] = os.path.getsize(the_file)
  response["Content-Disposition"] = f"attachment; filename={filename}"
  return response


class ContactView(LoginRequiredMixin, generic.FormView):
  template_name = "cm_main/contact/contact-form.html"
  form_class = ContactForm
  success_url = "/"
  _admin = None

  def admin(self):
    if self._admin is None:
      self._admin = get_user_model().objects.filter(is_superuser=True).first()
    return self._admin

  def get_context_data(self, **kwargs):
    return {'site_admin': self.admin().get_full_name(), 'form': self.form_class()}

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST, request.FILES)
    if form.is_valid():
      # send an email to the admin (ie first superuser)
      sender = get_user(request)
      title = _("You have a new message from %(name)s (%(email)s). ") % {
           "name": sender.get_full_name(), "email": sender.email}
      email = EmailMultiAlternatives(
        _("Contact form"),
        title + _("But your mailer tools is too old to show it :'("),
        sender.email,
        [self.admin().email],
      )
      # attach an HTML version of the message
      html_message = render_to_string('cm_main/contact/email-contact-form.html', {
        'title': title,
        'sender': sender,
        'message': form.cleaned_data['message'],
        'site_name': settings.SITE_NAME,
      })
      email.attach_alternative(html_message, "text/html")

      # attach the uploaded file if any
      if 'attachment' in request.FILES:
        uploaded_file = request.FILES.get('attachment')
        if isinstance(uploaded_file, InMemoryUploadedFile) or isinstance(uploaded_file, TemporaryUploadedFile):
          email.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
        else:
          raise ValueError(_("This file type is not supported"))

      # and send the email
      email.send(fail_silently=False)

      messages.success(request, _("Your message has been sent"))

    return render(request, self.template_name, {'form': form})


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


def get_github_release_version(owner, repo):
    """
    Retrieves the latest release version of a GitHub repository.

    :param owner: Repository owner
    :param repo: Repository name
    :return: Version of latest release or None if not found
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)

    print("version github response:", response)

    if response.status_code == 200:
        data = response.json()
        return data['tag_name']
    else:
        return _("Error: %s") % response.status_code


@login_required
def statistics(request):
  admin = Member.objects.filter(is_superuser=True).first()
  latest_release = get_github_release_version('leolivier', 'cousins-matter')
  if latest_release != settings.APP_VERSION:
    release_warning = _("Your version is not up-to-date, please update it.")
    latest_release = {
      'value': latest_release,
      'warning': release_warning
    }
  else:
    latest_release = {
      'value': latest_release,
      'info': _("Your version is up-to-date.")
    }

  stats = {
    _('Site'): {
      _('Site name'): settings.SITE_NAME,
      _('Site URL'): request.build_absolute_uri('/'),
      _('Application Version'): settings.APP_VERSION,
      _('Latest release'): latest_release,
    },
    _('Members'): {
      _('Total number of members'): Member.objects.count(),
      _('Number of active members'): Member.objects.filter(is_active=True).count(),
      _('Number of managed members'): Member.objects.filter(is_active=False).count(),
    },
    _('Galleries'): {
      _('Number of galleries'): Gallery.objects.count(),
      _('Number of photos'): Photo.objects.count(),
    },
    _("Forums"): {
      _('Number of posts'): Post.objects.count(),
      _('Number of post messages'): Message.objects.count(),
      _('Number of message comments'): Comment.objects.count(),
    },
    _("Chats"): {
      _('Number of chat rooms'): ChatRoom.objects.count(),
      _('Number of chat messages'): ChatMessage.objects.count(),
    },
    _('Administrator'): {
      _('This site is managed by'): admin.get_full_name(),
      _('Administrator email'): admin.email,
    },
  }
  return render(request, 'cm_main/about/site-stats.html', {'stats': stats})
