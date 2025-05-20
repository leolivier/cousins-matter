from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from classified_ads.forms import AdPhotoForm, ClassifiedAdForm
from cm_main.utils import assert_request_is_ajax

from .models import AdPhoto, ClassifiedAd, Categories


class CreateAdView(LoginRequiredMixin, generic.CreateView):
    model = ClassifiedAd
    template_name = 'classified_ads/form.html'
    form_class = ClassifiedAdForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, _("Classified ad created successfully"))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categories()
        return context

    def get_success_url(self):
        # Par exemple, rediriger vers la page de détail de l'objet nouvellement créé.
        return reverse('classified_ads:detail', args=[self.object.pk])


class UpdateAdView(LoginRequiredMixin, generic.UpdateView):
    model = ClassifiedAd
    template_name = 'classified_ads/form.html'
    form_class = ClassifiedAdForm

    def get_success_url(self):
        # Par exemple, rediriger vers la page de détail de l'objet nouvellement créé.
        return reverse('classified_ads:detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        if self.request.user != self.get_object().owner:
            raise PermissionDenied
        context = super().get_context_data(**kwargs)
        context['categories'] = Categories()
        context['photo_form'] = AdPhotoForm()
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Classified ad updated successfully"))
        return super().form_valid(form)


class DeleteAdView(LoginRequiredMixin, generic.View):

  model = ClassifiedAd

  def post(self, request, pk):
    ad = get_object_or_404(self.model, pk=pk)
    if self.request.user != ad.owner:
      raise PermissionDenied
    ad.delete()
    messages.success(request, _("Ad \"%(title)s\" deleted") % {"title": ad.title})
    return redirect("classified_ads:list")


class ListAdsView(LoginRequiredMixin, generic.ListView):
    model = ClassifiedAd
    template_name = 'classified_ads/list.html'

    def get_queryset(self):
        return ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).order_by('-date_created')


class AdDetailView(LoginRequiredMixin, generic.DetailView):
    model = ClassifiedAd
    template_name = 'classified_ads/detail.html'


class AdPhotoAddView(LoginRequiredMixin, generic.View):
    def post(self, request, pk):
        form = AdPhotoForm(request.POST, self.request.FILES)
        if form.is_valid():
            form.instance.ad = get_object_or_404(ClassifiedAd, pk=self.kwargs['pk'])
            form.save()
            messages.success(self.request, _("Photo added successfully"))
        return redirect('classified_ads:update', pk=self.kwargs['pk'])


@login_required
@csrf_exempt
def delete_photo(request, pk):
    assert_request_is_ajax(request)
    photo = get_object_or_404(AdPhoto, pk=pk)
    photo.delete()
    return JsonResponse({'success': True})


@login_required
def send_message(request, pk):
    # ad = ClassifiedAd.objects.get(pk=pk)
    # Send a message to the ad owner by email
    return redirect('classified_ads')
