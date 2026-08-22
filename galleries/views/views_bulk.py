import logging
import shutil
import uuid

from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import generic
from django.utils.translation import gettext as _

from django_q.tasks import result_group, count_group

from core.htmx import htmx_refresh

from ..forms import BulkUploadPhotosForm
from ..tasks import ZipImport
from ..services import handle_zip

logger = logging.getLogger(__name__)


class BulkUploadPhotosView(generic.FormView):
  template_name = "galleries/bulk_upload.html"
  form_class = BulkUploadPhotosForm
  success_url = reverse_lazy("galleries:galleries")

  def post(self, request, *args, **kwargs):
    # print("post bulk upload")
    form = BulkUploadPhotosForm(request.POST, request.FILES)
    if form.is_valid():
      try:
        zip_file = request.FILES["zipfile"]
        # task_group = request.POST.get("csrfmiddlewaretoken")  # not generated in test context
        task_group = uuid.uuid4().hex
        zimport = handle_zip(zip_file, task_group, request.user.id, form.cleaned_data.get("gallery"))
        hx_get_url = reverse("galleries:upload_progress", args=(task_group,))
        logger.debug(f"rendering first progress-bar url: {hx_get_url}")
        return render(
          request,
          "core/common/progress-bar.html",
          {"hx_get": hx_get_url, "frequency": "1s", "value": 0, "max": zimport.nbPhotos, "text": "0%"},
          status=200,
        )
        # print("post upload progress returns", r.content)
        # return r
      except ValidationError as e:
        for err in e.messages:
          messages.error(request, err)
      except Exception as e:
        messages.error(request, e.__str__())
    else:
      for code, error in form.errors.items():
        messages.error(request, ": ".join(code, error))
    return htmx_refresh()


def upload_progress(request, id):
  zimport = ZipImport.get(id)
  logger.debug(f"upload progress group: {id}, zimport: {zimport}")
  if not zimport:  # removed from the list when completed
    raise Http404(_("Upload not found"))
  value = count_group(id)
  max = zimport.nbPhotos

  # get already finished tasks
  results = result_group(id, failures=True, count=value, cached=False)
  # print error messages first then successful import
  if results:
    for photo_path, errors in results:
      if photo_path:
        zimport.photos.add(photo_path)
      if errors:
        for err in errors:
          zimport.errors.add(err)
  context = {
    "hx_get": request.get_full_path(),
    "frequency": "1s",
    "value": value,
    "max": max,
    "text": str(int(value * 100 / max)) + "%",
    "processed_objects": zimport.photos,
    "errors": zimport.errors,
  }
  if value == max:  # reached the end
    context["back_url"] = reverse("galleries:galleries")
    context["back_text"] = _("Back to galleries list")
    context["success"] = _("Zip file uploaded: %(lg)d galleries and %(nbp)d photos created") % {
      "lg": zimport.nbGalleries,
      "nbp": len(zimport.photos),
    }
    # clean temp directory
    shutil.rmtree(zimport.root)
    # remove zimport from the cache
    zimport.unregister()
    logger.debug(f"cleaned {zimport}")
  logger.debug(
    f"upload progress bar value: {value}, max: {max}, processed objects: {zimport.photos}, errors: {zimport.errors}"
  )
  return render(request, "core/common/progress-bar.html", context)
