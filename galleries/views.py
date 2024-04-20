import logging
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.db.models import OuterRef
from .models import Gallery, Photo

logger = logging.getLogger(__name__)

class GalleryCreateView(LoginRequiredMixin, generic.CreateView):

	template_name = "galleries/edit_gallery.html"
	model = Gallery
	fields = ["name", "description", "cover", "parent"]
# TODO: check slug uniqueness

class GalleryUpdateView(LoginRequiredMixin, generic.UpdateView):

	template_name = "galleries/edit_gallery.html"
	model = Gallery
	fields = ["name", "description", "cover", "parent"]

class GalleryDisplayView(LoginRequiredMixin, generic.DetailView):
	template_name = "galleries/show_gallery.html"
	model = Gallery
	fields = "__all__"
# TODO: is this get needed?
	def get(self, request, pk): # TODO manage slug instead of pk
		gallery = get_object_or_404(Gallery, pk=pk)
		return render(request, self.template_name, context={ "gallery": gallery })

class GalleryTreeView(LoginRequiredMixin, generic.ListView):
	template_name = "galleries/galleries_tree.html"
	model = Gallery

	def get_context_data(self, **kwargs):
		galleries = Gallery.objects.filter(parent=None)
		return { "galleries": galleries}
	
class PhotoDetailView(LoginRequiredMixin, generic.DetailView):
	template_name = "galleries/photo_detail.html"
	model = Photo
	def get_queryset(self):
		return Photo.objects.annotate(
			previous_id=Photo.objects.filter(
				id__lt=OuterRef("id"),
				gallery=OuterRef("gallery")
			).order_by("-id").values("id")[:1],
			next_id=Photo.objects.filter(
				id__gt=OuterRef("id"),
				gallery=OuterRef("gallery")
			).order_by("id").values("id")[:1],
		).filter(id=self.kwargs['pk'])
	
class PhotoAddView(LoginRequiredMixin, generic.CreateView):
	template_name = "galleries/edit_photo.html"
	model = Photo
	fields = ["name", "description", "image", "date", "gallery"]

	def post(self, request: HttpRequest, gallery, *args, **kwargs) -> HttpResponse:
		form = self.get_form()
		if form.is_valid():
			form.instance.gallery_id = form.instance.gallery_id or gallery
			photo = form.save()
			if 'create-and-add' in request.POST:
				messages.success(request, _("Photo created"))
				return redirect("galleries:add_photo", gallery)
			else:
				redirect("galleries:photo", gallery, photo.id)
		
		return super().post(request, *args, **kwargs)	
