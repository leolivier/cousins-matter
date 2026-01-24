from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh

from classified_ads.forms import AdPhotoForm, ClassifiedAdForm, MessageForm
from cm_main.utils import check_edit_permission

from .models import AdPhoto, ClassifiedAd, Categories


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
    return render(
      request,
      "cm_main/common/confirm-delete-modal-htmx.html",
      {
        "ays_title": _("Classified ads deletion"),
        "ays_msg": _('Are you sure you want to delete the classified ad "%(title)s"?') % {"title": ad.title},
        "delete_url": request.get_full_path(),
        "expected_value": ad.title,
      },
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
    return ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).order_by("-date_created")


class AdDetailView(generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"


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


def delete_photo(request, pk):
  photo = get_object_or_404(AdPhoto, pk=pk)
  ad = photo.ad
  if request.method == "POST":
    check_edit_permission(request, photo.ad.owner)
    photo.delete()
    # # as the swap is delete below, we don't care of the reponse (but status must be ok)
    # return HttpResponse(status=200, content="<div>ok</div>")
    return render(request, "classified_ads/gallery.html", {"edit_gallery": True, "ad": ad})
  return render(
    request,
    "cm_main/common/confirm-delete-modal-htmx.html",
    {
      "ays_title": _("Photo deletion"),
      "ays_msg": _("Are you sure you want to delete this photo?"),
      "delete_url": request.get_full_path(),
      # "hx_params": f"hx-target=#photo-{photo.id} hx-swap=delete"
      "hx_params": "hx-target=#ad-photos hx-swap=outerHTML",
    },
  )


def send_message(request, pk):
  ad = get_object_or_404(ClassifiedAd, pk=pk)
  if request.method == "POST":
    # Send a message to the ad owner by email
    email = ad.owner.email
    subject = _("Message from %(username)s about ad %(title)s") % {
      "username": request.user.full_name,
      "title": ad.title,
    }
    message = _("""Hello %(recipient)s,
%(username)s sent you the following message about ad %(title)s:
==========
%(message)s
==========
You can reply to him/her directly at this address: %(email)s.
Best,
The %(site_name)s admin team

%(site_url)s
""") % {
      "recipient": ad.owner.full_name,
      "username": request.user.full_name,
      "title": ad.title,
      "message": request.POST.get("message"),
      "site_name": settings.SITE_NAME,
      "site_url": settings.SITE_DOMAIN,
      "email": request.user.email,
    }
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    messages.success(request, _("Message sent successfully"))
    return HttpResponseClientRefresh()
  return render(request, "classified_ads/send-message.html", {"form": MessageForm(), "ad": ad})


def get_subcategories(request):
  category = request.GET.get("category")
  subcategories = [("", _("Select a subcategory")), *Categories.list_subcategories(category)]
  return render(request, "classified_ads/form.html#subcategories", {"subcategories": subcategories})
