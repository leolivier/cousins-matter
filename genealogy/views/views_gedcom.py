from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from ..forms import GedcomImportForm
from ..utils import GedcomParser, GedcomExporter, clear_genealogy_caches


def import_gedcom(request):
  if request.method == "POST":
    form = GedcomImportForm(request.POST, request.FILES)
    if form.is_valid():
      gedcom_file = request.FILES["gedcom_file"]
      # Save temporary file
      path = default_storage.save("tmp/" + gedcom_file.name, ContentFile(gedcom_file.read()))
      full_path = os.path.join(default_storage.location, path)

      try:
        parser = GedcomParser(full_path)
        parser.parse()
        messages.success(request, _("GEDCOM imported successfully."))
        clear_genealogy_caches()
      except Exception as e:
        messages.error(request, _("Error importing GEDCOM: %(error)s") % {"error": str(e)})
      finally:
        default_storage.delete(path)

      return redirect("genealogy:dashboard")
  else:
    form = GedcomImportForm()
  return render(request, "genealogy/import_gedcom.html", {"form": form})


def export_gedcom(request):
  exporter = GedcomExporter()
  gedcom_content = exporter.export()
  response = HttpResponse(gedcom_content, content_type="text/gedcom")
  response["Content-Disposition"] = f'attachment; filename="{settings.GEDCOM_FILE}"'
  return response


def download_gedcom(request):
  exporter = GedcomExporter()
  gedcom_content = exporter.export()
  return HttpResponse(gedcom_content, content_type="text/plain")
