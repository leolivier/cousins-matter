import logging
from django.views import generic
from django_htmx.http import HttpResponseClientRefresh
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from ..models import Address
from ..forms import AddressUpdateForm

logger = logging.getLogger(__name__)


class AddressDetailView(generic.DetailView):
  model = Address
  template_name = "members/address/address_detail.html"


class AddressCreateView(generic.CreateView):
  model = Address
  template_name = "members/address/address_form.html"
  fields = "__all__"


class AddressUpdateView(generic.UpdateView):
  model = Address
  template_name = "members/address/address_form.html"
  fields = "__all__"


class ModalAddressMixin:
  model = Address
  template_name = "members/address/address_form.html"
  form_class = AddressUpdateForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title
    return context

  def process_form(self, request, form):
    assert request.htmx
    if form.is_valid():
      address = form.save()
      addresses = Address.objects.all()
      return render(
        request, "members/address/address_form.html#set_address", {"selected_address": address, "addresses": addresses}
      )
    else:
      messages.error(request, form.errors)
      return HttpResponseClientRefresh()


class ModalAddressCreateView(ModalAddressMixin, generic.CreateView):
  title = _("New Address")

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST)
    return self.process_form(request, form)


class ModalAddressUpdateView(ModalAddressMixin, generic.UpdateView):
  title = _("Change Address")

  def post(self, request, *args, **kwargs):
    address = get_object_or_404(Address, pk=kwargs["pk"])
    form = AddressUpdateForm(request.POST, instance=address)
    return self.process_form(request, form)
