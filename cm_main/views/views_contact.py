import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views import generic
from ..forms import ContactForm

logger = logging.getLogger(__name__)


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
    return {'site_admin': self.admin().full_name, 'form': self.form_class()}

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST, request.FILES)
    if form.is_valid():
      # send an email to the admin (ie first superuser)
      sender = get_user(request)
      title = _("You have a new message from %(name)s (%(email)s). ") % {
           "name": sender.full_name, "email": sender.email}
      email = EmailMultiAlternatives(
        subject=_("Contact form"),
        body=title + _("But your mailer tools is too old to show it :'("),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[self.admin().email],
        reply_to=[sender.email],
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
      return redirect(self.success_url)

    return render(request, self.template_name, {'form': form})
