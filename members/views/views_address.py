import logging
from django.views import generic
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from ..models import Address
from ..forms import AddressUpdateForm
from cm_main.utils import assert_request_is_ajax

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


def _json_address_response(address):
    res = {}
    res["address_id"] = address.id
    res["number_and_street"] = address.number_and_street
    res["complementary_info"] = address.complementary_info
    res["zip_code"] = address.zip_code
    res["city"] = address.city
    res["country"] = address.country
    res["address_str"] = str(address)
    return JsonResponse(res, status=200)


class ModalAddressMixinView(LoginRequiredMixin):
    model = Address
    template_name = "members/address/address_form.html"
    fields = "__all__"

    def process_form(self, request, form):
        assert_request_is_ajax(request)
        if form.is_valid():
            address = form.save()
            return _json_address_response(address)
        else:
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)


class ModalAddressCreateView(ModalAddressMixinView, generic.CreateView):
    def post(self, request, *args, **kwargs):
        # create a form instance from the request and save it
        form = AddressUpdateForm(request.POST)
        return self.process_form(request, form)


class ModalAddressUpdateView(ModalAddressMixinView, generic.UpdateView):
    def post(self, request, *args, **kwargs):
        address = get_object_or_404(Address, pk=kwargs["pk"])
        # create a form instance and populate it with data from the request on existing member (or None):
        form = AddressUpdateForm(request.POST, instance=address)
        return self.process_form(request, form)


@login_required
def get_address(request, pk):
    assert_request_is_ajax(request)
    address = get_object_or_404(Address, pk=pk)
    return _json_address_response(address)
