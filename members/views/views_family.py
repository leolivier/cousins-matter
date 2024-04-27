import logging
# from pprint import pprint
from django.views import generic
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect

from ..models import Family
from ..forms import FamilyUpdateForm
from cousinsmatter.utils import is_ajax, redirect_to_referer

logger = logging.getLogger(__name__)

class FamilyDetailView(LoginRequiredMixin, generic.DetailView):
   model = Family

class FamilyCreateView(LoginRequiredMixin, generic.CreateView):
   model = Family
   form_class = FamilyUpdateForm
   fields = "__all__"

class FamilyUpdateView(LoginRequiredMixin, generic.UpdateView):
   model = Family
   form_class = FamilyUpdateForm
   fields = "__all__"

class ModalFamilyCreateView(LoginRequiredMixin, generic.CreateView):
   model = Family
   fields = "__all__"
   def post(self, request, *args, **kwargs):
      if is_ajax(request):
         # create a form instance from the request and save it
         form = FamilyUpdateForm(request.POST)
         if form.is_valid():
            family = form.save()
            return JsonResponse({"family_id": family.id, "family_name": family.str()}, status=200)
         else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)

      return redirect_to_referer(request)

class ModalFamilyUpdateView(LoginRequiredMixin, generic.UpdateView):
   model = Family
   fields = "__all__"
   def post(self, request, *args, **kwargs):
      family = get_object_or_404(Family, pk=kwargs['pk'])
      if is_ajax(request):
         # create a form instance and populate it with data from the request on existing member (or None):
         form = FamilyUpdateForm(request.POST, instance=family)
         if form.is_valid():
            family = form.save()
            return JsonResponse({"family_id": family.id, "family_name": family.str()}, status=200)
         else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)

      return redirect_to_referer(request)
