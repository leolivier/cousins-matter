import logging
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Case, DateField, F, IntegerField, Value, When
from django.db.models.functions import Cast, ExtractDay, ExtractMonth
from django.utils.translation import gettext as _

from verify_email.email_handler import send_verification_email

from core.utils import MakeDate
from ..models import Member

logger = logging.getLogger(__name__)


def do_activate_member(member, request):
  """activate the member with username"""
  if member.is_dead:
    return ("error", _("Error: Cannot activate a dead member"))
  elif member.is_active:
    if member.member_manager is not None:
      member.member_manager = None
      member.save()
    return ("error", _("Error: Member already active"))
  elif not member.email:
    return ("error", _("Error: Member without email cannot be activated"))
  else:
    send_verification_email(request, inactive_user=member)
    logger.info(f"Member {member.username} activated by {request.user.username}")
    return (
      "success",
      _(
        "Member account successfully activated. The owner of the account will now receive an email "
        "containing an activation link then will be redirected to the password reset screen."
      ),
    )


def get_birthdays(ndays):
  """
  Return the members with their birthday in the next ndays days
  (or previous ndays days if ndays <0)
  """
  today = date.today()
  beg_date = today  # - timedelta(days=1)
  end_date = today + timedelta(days=ndays)
  current_year = today.year

  members = (
    Member.objects
    .only("id", "first_name", "last_name", "birthdate")
    .filter(is_dead=False)
    .annotate(
      this_year_birthday=Case(
        # Manages only Feb 29th bithdate when the current year is not a leap year
        # i.e. on a non-leap year, a Feb 29th bithdate is considered as a Feb 28th birthdate
        When(
          birthdate__month=2,
          birthdate__day=29,
          then=MakeDate(
            Value(current_year),
            Value(2),
            Value(28 if current_year % 4 != 0 else 29),
          ),
        ),
        default=MakeDate(
          Value(current_year),
          Cast(ExtractMonth(F("birthdate")), output_field=IntegerField()),
          Cast(ExtractDay(F("birthdate")), output_field=IntegerField()),
        ),
        output_field=DateField(),
      )
    )
    .filter(this_year_birthday__range=(beg_date, end_date))
    .order_by("this_year_birthday")
  )

  bdays = []
  for m in members:
    delta = (m.this_year_birthday - today).days
    bdays.append((m, delta))
  return bdays


def get_members_page_queryset(query, sort_by: str | None, order: str):
  members = Member.objects
  members = members.fuzzy_search(query) if query else members.all()
  sort_by = [sort_by] if sort_by else ["last_name", "first_name"]  # default sort
  if order:
    sort_by = [order + s for s in sort_by]
  return members.order_by(*sort_by)


def do_init_member(member: Member, user_id: int):
  # if new managed member is created, it must be inactivated
  member.is_active = False
  # force member_manager to the logged in user
  member.member_manager = Member.objects.get(id=user_id)
  member.save(update_fields=["is_active", "member_manager"])


def do_notify_death(dead_member: Member, sender: Member, deathdate: date, message: str):
  # Send email to admins
  emails = list(
    Member.objects.filter(is_superuser=True, email__isnull=False).exclude(email="").values_list("email", flat=True)
  )

  if emails:
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    subject = _("Death notification for %(member)s") % {"member": dead_member.full_name}
    email_context = {
      "member": dead_member,
      "sender": sender,
      "deathdate": deathdate,
      "message": message,
      "site_name": settings.SITE_NAME,
    }

    html_message = render_to_string("members/email/notify_death_email.html", email_context)
    plain_message = render_to_string("members/email/notify_death_email.html", email_context)  # simplify for now, or strip tags

    from django.utils.html import strip_tags

    plain_message = strip_tags(html_message)

    send_mail(
      subject,
      plain_message,
      settings.DEFAULT_FROM_EMAIL,
      emails,
      html_message=html_message,
    )


def do_toggle_follow(followed: Member, follower: Member, follower_url: str):

  if followed == follower:
    return ("error", _("You can't follow yourself!"))
  elif followed.followers.filter(id=follower.id).exists():
    followed.followers.remove(follower)
    # no notification here?
    return ("success", _("You are no longer following %(followed_name)s") % {"followed_name": followed.full_name})
  elif followed.is_dead:
    return ("error", _("Error: You can't follow dead people"))
  else:
    followed.followers.add(follower)
    # send email to followed to tell him/her someone is following him/her
    title = _("You have a new follower!")
    message = _("%(follower_name)s is now following you!") % {"follower_name": follower.full_name}

    from django.template.loader import render_to_string
    from django.core.mail import send_mail

    send_mail(
      title,
      message,
      settings.DEFAULT_FROM_EMAIL,
      [followed.email],
      html_message=render_to_string(
        "members/email/new_follower.html",
        {
          "title": title,
          "follower_name": follower.full_name,
          "followed_name": followed.full_name,
          "follower_url": follower_url,
          "site_name": settings.SITE_NAME,
        },
      ),
    )
    return ("success", _("You are now following %(followed_name)s") % {"followed_name": followed.full_name})
