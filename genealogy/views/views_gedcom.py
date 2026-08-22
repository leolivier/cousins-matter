from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from ..forms import GedcomImportForm
from ..services import do_import_gedcom
from ..utils import GedcomExporter


def import_gedcom(request):
  if request.method == "POST":
    form = GedcomImportForm(request.POST, request.FILES)
    if form.is_valid():
      success, message = do_import_gedcom(request.FILES["gedcom_file"])
      if success:
        messages.success(request, message)
      else:
        messages.error(request, message)
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
