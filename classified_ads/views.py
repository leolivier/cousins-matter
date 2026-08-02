from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh

from classified_ads.forms import AdPhotoForm, ClassifiedAdForm, MessageForm
from core.utils import check_edit_permission, confirm_delete_modal

from .models import AdPhoto, Categories, ClassifiedAd
from .services import do_send_ad_message, get_next_prev_photo


class CreateAdView(generic.CreateView):
  model = ClassifiedAd
  template_name = "classified_ads/form.html"
  form_class = ClassifiedAdForm

  def form_valid(self, form):
    form.instance.owner = self.request.user
    messages.success(self.request, _("Classified ad created successfully"))
    return super().form_valid(form)

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["categories"] = Categories()
    return context

  def get_success_url(self):
    # Par exemple, rediriger vers la page de détail de l'objet nouvellement créé.
    return reverse("classified_ads:detail", args=[self.object.pk])


class UpdateAdView(generic.UpdateView):
  model = ClassifiedAd
  template_name = "classified_ads/form.html"
  form_class = ClassifiedAdForm

  def get_success_url(self):
    return reverse("classified_ads:detail", args=[self.object.pk])

  def get_context_data(self, **kwargs):
    check_edit_permission(self.request, self.get_object().owner)
    context = super().get_context_data(**kwargs)
    context["categories"] = Categories()
    return context

  def form_valid(self, form):
    messages.success(self.request, _("Classified ad updated successfully"))
    return super().form_valid(form)


class DeleteAdView(generic.View):
  model = ClassifiedAd

  def get(self, request, pk):
    ad = get_object_or_404(self.model, pk=pk)
    return confirm_delete_modal(
      request,
      _("Classified ads deletion"),
      _('Are you sure you want to delete the classified ad "%(title)s"?') % {"title": ad.title},
      expected_value=ad.title,
    )

  def post(self, request, pk):
    ad = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, ad.owner)
    ad.delete()
    messages.success(request, _('Ad "%(title)s" deleted') % {"title": ad.title})
    return HttpResponseClientRedirect(reverse("classified_ads:list"))


class ListAdsView(generic.ListView):
  model = ClassifiedAd
  template_name = "classified_ads/list.html"

  def get_queryset(self):
    return (
      ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).select_related("owner").order_by("-date_created")
    )


class AdDetailView(generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"

  def get_queryset(self):
    return ClassifiedAd.objects.select_related("owner").prefetch_related("photos")


class AdPhotoAddView(generic.View):
  def get(self, request, pk):
    ad = get_object_or_404(ClassifiedAd, pk=pk)
    check_edit_permission(request, ad.owner)
    return render(request, "classified_ads/photo-form.html", {"form": AdPhotoForm(), "ad_id": ad.pk})

  def post(self, request, pk):
    form = AdPhotoForm(request.POST, self.request.FILES)
    if form.is_valid():
      form.instance.ad = get_object_or_404(ClassifiedAd, pk=pk)
      check_edit_permission(request, form.instance.ad.owner)
      form.save()
      # redraw only the image gallery
      return render(request, "classified_ads/gallery.html", {"edit_gallery": True, "ad": form.instance.ad})
    else:
      messages.error(self.request, _("Photo not added: %(errors)s") % {"errors": form.errors})
      return HttpResponseClientRefresh()


def get_fullscreen_photo(request, pk):
  assert request.htmx  # nosec B101
  try:
    photo = get_next_prev_photo(pk, request.GET.get("side"))
  except AdPhoto.DoesNotExist:
    messages.error(request, _("Photo not found"))
    return HttpResponseClientRedirect(reverse("classified_ads:list"))

  return render(
    request,
    "galleries/photo_fullscreen.html#image",
    {
      "swipe_url": reverse("classified_ads:get_fullscreen_photo", args=[photo.id]),
      "fullscreen_url": photo.image.url,
      "pk": photo.id,
    },
  )


def delete_photo(request, pk):
  photo = get_object_or_404(AdPhoto, pk=pk)
  ad = photo.ad
  if request.method == "POST":
    check_edit_permission(request, photo.ad.owner)
    photo.delete()
    # # as the swap is delete below, we don't care of the reponse (but status must be ok)
    # return HttpResponse(status=200, content="<div>ok</div>")
    return render(request, "classified_ads/gallery.html", {"edit_gallery": True, "ad": ad})

  return confirm_delete_modal(
    request,
    _("Photo deletion"),
    _("Are you sure you want to delete this photo?"),
    hx_params="hx-target=#ad-photos hx-swap=outerHTML",
  )


def send_message(request, pk):
  ad = get_object_or_404(ClassifiedAd, pk=pk)
  if request.method == "POST":
    do_send_ad_message(request.user, ad, request.POST.get("message"))
    messages.success(request, _("Message sent successfully"))
    return HttpResponseClientRefresh()
  return render(request, "classified_ads/send-message.html", {"form": MessageForm(), "ad": ad})


def get_subcategories(request):
  category = request.GET.get("category")
  subcategories = [("", _("Select a subcategory")), *Categories.list_subcategories(category)]
  return render(request, "classified_ads/form.html#subcategories", {"subcategories": subcategories})
