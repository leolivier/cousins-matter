import logging
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from ..models import Address
from ..forms import AddressUpdateForm
from cousinsmatter.utils import assert_request_is_ajax

logger = logging.getLogger(__name__)


class AddressDetailView(LoginRequiredMixin, generic.DetailView):
    model = Address
    template_name = "members/address/address_detail.html"


class AddressCreateView(LoginRequiredMixin, generic.CreateView):
    model = Address
    template_name = "members/address/address_form.html"
    fields = "__all__"


class AddressUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Address
    template_name = "members/address/address_form.html"
    fields = "__all__"


class ModalAddressCreateView(LoginRequiredMixin, generic.CreateView):
    model = Address
    template_name = "members/address/address_form.html"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
      assert_request_is_ajax(request)
      # create a form instance from the request and save it
      form = AddressUpdateForm(request.POST)
      # form = self.get_form()
      if form.is_valid():
        address = form.save()
        return JsonResponse({"address_id": address.id, "address_str": str(address)}, status=200)
      else:
        errors = form.errors.as_json()
        return JsonResponse({"errors": errors}, status=400)


class ModalAddressUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Address
    template_name = "members/address/address_form.html"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
      assert_request_is_ajax(request)
      address = get_object_or_404(Address, pk=kwargs['pk'])
      # create a form instance and populate it with data from the request on existing member (or None):
      form = AddressUpdateForm(request.POST, instance=address)
      # form = self.get_form()
      if form.is_valid():
        address = form.save()
        return JsonResponse({"address_id": address.id, "address_str": str(address)}, status=200)
      else:
        errors = form.errors.as_json()
        return JsonResponse({"errors": errors}, status=400)
