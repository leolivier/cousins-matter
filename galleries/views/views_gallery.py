import logging
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Gallery

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
	

