import requests
from datetime import timedelta
from ipware import get_client_ip
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import FieldDoesNotExist
from django.db.models.signals import post_migrate
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import schedule
from django_q.models import Schedule
from functools import lru_cache
from members.models import LoginTrace

default_geolocation_data = None


@receiver(user_logged_in)
def post_login(sender, user, request, **kwargs):
    client_ip, is_routable = get_client_ip(request)
    result = None
    mapped_fields = {}

    result = (
        get_default_geolocation_data()
        if (not client_ip or client_ip == "127.0.0.1")
        else get_geolocation_data(client_ip)
        if is_routable
        else {"error": True, "reason": "Address not routable"}
    )
    client_ip = (
        client_ip or settings.LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP
    )  # for tests only
    assert isinstance(result, dict)
    for key, value in result.items():
        if key in ["user", "ip", "user_agent", "ip_info", "created_at"]:
            continue
        try:
            _ = LoginTrace._meta.get_field(key)
            mapped_fields[key] = value
        except FieldDoesNotExist:
            pass
    _ = LoginTrace.objects.create(
        user=user,
        ip=client_ip,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        ip_info=result,
        **mapped_fields,
    )


@receiver(user_logged_out)
def post_logout(sender, user, **kwargs):
    last_login = LoginTrace.objects.filter(user=user).order_by("-login_at").first()
    if last_login and not last_login.logout_at:
        last_login.logout_at = timezone.now()
        last_login.save()


@lru_cache(maxsize=128)
def get_geolocation_data(ip: str):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        response.raise_for_status()  # Checks if the request was successful
        return response.json()  # Try to decode the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return {"error": True, "reason": f"Error during request: {e}"}
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
        return {"error": True, "reason": f"Error decoding JSON: {e}"}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": True, "reason": f"An error occurred: {e}"}


def get_default_geolocation_data():
    global default_geolocation_data
    if default_geolocation_data is None:
        default_geolocation_data = get_geolocation_data(
            settings.LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP
        )
    return default_geolocation_data


def purge_login_traces(days: int):
  "Deletes login traces older than days."
  a_while_ago = timezone.now() - timedelta(days=days)
  # Deletion of logs with a login date prior to LOGIN_HISTORY_PURGE_DAYS days ago
  deleted, _ = LoginTrace.objects.filter(login_at__lt=a_while_ago).delete()
  return deleted


_purge_scheduled = False


# starts the scheduling after the migrations
# TODO: make sure the post_migrate signals (1 per migration) are sent after all migrations are done
@receiver(post_migrate)  # noqa E302
def schedule_purge_login_traces(sender, **kwargs):
    "Schedules the purge_login_traces function to run weekly."
    global _purge_scheduled
    if _purge_scheduled:
        return
    _purge_scheduled = True
    try:
        if not Schedule.objects.filter(name="purge_login_traces").exists():
            schedule(
                "members.trace_login.purge_login_traces",
                settings.LOGIN_HISTORY_PURGE_DAYS,
                schedule_type=Schedule.WEEKLY,
                name="purge_login_traces",
            )
    except IntegrityError as e:
        print(f"Error scheduling purge_login_traces: {e}")
