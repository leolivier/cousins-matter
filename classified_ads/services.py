from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _

from .models import AdPhoto
from tenants.settings_overrides import tenant_setting


def get_next_prev_photo(pk, side):
  # this raises AdPhoto.DoesNotExist if the photo doesn't exist
  ad_id = AdPhoto.objects.only("ad_id").get(pk=pk).ad_id
  photo = AdPhoto.objects.filter(ad=ad_id).order_by("id")

  match side:
    case "prev":
      photo = photo.filter(id__lt=pk).last()
    case "next":
      photo = photo.filter(id__gt=pk).first()
    case None:
      photo = photo.get(id=pk)
    case _:
      raise ValueError("Invalid side: %s" % side)

  return photo or AdPhoto.objects.get(id=pk)


def do_send_ad_message(sender, ad, message_text):
  """Email ``ad``'s owner a ``message_text`` from ``sender``.

  ``send_mail`` runs with ``fail_silently=False``: an SMTP error raises instead
  of returning a failure flag, so there is no soft-failure path to report.
  """
  subject = _("Message from %(username)s about ad %(title)s") % {
    "username": sender.full_name,
    "title": ad.title,
  }
  message = _("""Hello %(recipient)s,
%(username)s sent you the following message about ad %(title)s:
==========
%(message)s
==========
You can reply to him/her directly at this address: %(email)s.
Best,
The %(site_name)s admin team

%(site_url)s
""") % {
    "recipient": ad.owner.full_name,
    "username": sender.full_name,
    "title": ad.title,
    "message": message_text,
    "site_name": tenant_setting("site_name"),
    "site_url": settings.SITE_DOMAIN,
    "email": sender.email,
  }
  send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [ad.owner.email], fail_silently=False)
