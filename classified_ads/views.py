from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from classified_ads.forms import AdPhotoForm, ClassifiedAdForm, MessageForm
from cm_main.utils import assert_request_is_ajax, check_edit_permission

from .models import AdPhoto, ClassifiedAd, Categories


class CreateAdView(LoginRequiredMixin, generic.CreateView):
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


class UpdateAdView(LoginRequiredMixin, generic.UpdateView):
  model = ClassifiedAd
  template_name = "classified_ads/form.html"
  form_class = ClassifiedAdForm

  def get_success_url(self):
    return reverse("classified_ads:detail", args=[self.object.pk])

  def get_context_data(self, **kwargs):
    check_edit_permission(self.request, self.get_object().owner)
    context = super().get_context_data(**kwargs)
    context["categories"] = Categories()
    context["photo_form"] = AdPhotoForm()
    return context

  def form_valid(self, form):
    messages.success(self.request, _("Classified ad updated successfully"))
    return super().form_valid(form)


class DeleteAdView(LoginRequiredMixin, generic.View):
  model = ClassifiedAd

  def post(self, request, pk):
    ad = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, ad.owner)
    ad.delete()
    messages.success(request, _('Ad "%(title)s" deleted') % {"title": ad.title})
    return redirect("classified_ads:list")


class ListAdsView(LoginRequiredMixin, generic.ListView):
  model = ClassifiedAd
  template_name = "classified_ads/list.html"

  def get_queryset(self):
    return ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).order_by("-date_created")


class AdDetailView(LoginRequiredMixin, generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["message_form"] = MessageForm()
    return context


class AdPhotoAddView(LoginRequiredMixin, generic.View):
  def post(self, request, pk):
    form = AdPhotoForm(request.POST, self.request.FILES)
    if form.is_valid():
      form.instance.ad = get_object_or_404(ClassifiedAd, pk=self.kwargs["pk"])
      check_edit_permission(request, form.instance.ad.owner)
      form.save()
      messages.success(self.request, _("Photo added successfully"))
    return redirect("classified_ads:update", pk=self.kwargs["pk"])


@login_required
@csrf_exempt
def delete_photo(request, pk):
  assert_request_is_ajax(request)
  photo = get_object_or_404(AdPhoto, pk=pk)
  check_edit_permission(request, photo.ad.owner)
  photo.delete()
  return JsonResponse({"success": True})


@login_required
def send_message(request, pk):
  # Send a message to the ad owner by email
  ad = get_object_or_404(ClassifiedAd, pk=pk)
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
  send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
  messages.success(request, _("Message sent successfully"))
  return redirect("classified_ads:detail", pk=pk)
