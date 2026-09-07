import logging
from urllib.error import HTTPError
from urllib.request import urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

import json
from packaging import version

from core.services import build_site_stats, run_env_checks, send_test_email

logger = logging.getLogger(__name__)


def get_github_release_version(request, owner, repo):
  """
  Retrieves the latest release version of a GitHub repository.

  :param request: Django request object
  :param owner: Repository owner
  :param repo: Repository name
  :return: JSON response with version of latest release or error message if not found
  """

  url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
  try:
    with urlopen(url) as response:  # nosec
      data = response.read()
      json_data = json.loads(data)
      if "tag_name" in json_data:
        return json_data["tag_name"]
      else:
        messages.error(request, _("Version not found"))
        return None
  except HTTPError as e:
    messages.error(request, e.msg)
    return None


def get_latest_release_text(request):
  latest_release = get_github_release_version(request, "leolivier", "cousins-matter")
  # print('latest_release', latest_release)
  if latest_release is not None:
    latest_version = version.parse(latest_release)
    current_version = version.parse(settings.APP_VERSION)
    if current_version < latest_version:
      release_warning = _("Your version is not up-to-date.")
      if request.user.is_superuser:
        release_warning += "<br>"
        release_warning += _("Please look at the documentation for updating.")
        release_warning = mark_safe(release_warning)  # nosec

      latest_release = {
        "value": latest_release,
        "warning": release_warning,
        "icon": "poop",
      }
    elif current_version == latest_version:
      latest_release = {
        "value": latest_release,
        "info": _("Your version is up-to-date."),
        "icon": "cool",
      }
    else:
      latest_release = {
        "value": latest_release,
        "warning": _("Your version is newer than the latest release (?!?)"),
        "icon": "confused",
      }
  else:
    latest_release = {"value": "?", "error": _("Version not found"), "icon": "poop"}

  return latest_release


def statistics(request):
  site_url = request.build_absolute_uri("/")
  release_text = get_latest_release_text(request)
  stats = build_site_stats(site_url, release_text)
  return render(request, "core/about/site-stats.html", {"stats": stats})


def env_check(request):
  """
  Platform-admin diagnostics page (superuser only).

  GET renders the environment probes; POST (test email button) sends a test
  email to the requesting superuser and redirects back (PRG pattern).
  Anonymous users are redirected to the login page, logged-in non-superusers
  (members and tenant admins) get a 403 - same semantics as OnlySuperuserMixin,
  without its multi-tenant requirement.
  """
  if not request.user.is_authenticated:
    return redirect_to_login(request.get_full_path())
  if not request.user.is_superuser:
    raise PermissionDenied(_("Only platform administrators can run the environment check."))
  if request.method == "POST":
    ok, detail = send_test_email(request.user)
    (messages.success if ok else messages.error)(request, detail)
    return redirect("core:env_check")
  return render(request, "core/env_check.html", {"checks": run_env_checks(), "email_to": request.user.email})
