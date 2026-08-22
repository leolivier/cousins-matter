import logging

from django.contrib import messages
from django.contrib.auth import get_user, get_user_model
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import generic
from ..forms import ContactForm
from ..services import do_send_contact_email

logger = logging.getLogger(__name__)


class ContactView(generic.FormView):
  template_name = "core/contact/contact-form.html"
  form_class = ContactForm
  success_url = "/"
  _admin = None

  def admin(self):
    if self._admin is None:
      self._admin = get_user_model().objects.filter(is_superuser=True).first()
    return self._admin

  def get_context_data(self, **kwargs):
    return {"site_admin": self.admin().full_name, "form": self.form_class()}

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST, request.FILES)
    if form.is_valid():
      # send an email to the admin (ie first superuser)
      do_send_contact_email(
        get_user(request),
        self.admin(),
        form.cleaned_data["message"],
        request.FILES.get("attachment"),
      )
      messages.success(request, _("Your message has been sent"))
      return redirect(self.success_url)

    return render(request, self.template_name, {"form": form})
