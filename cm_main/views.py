from django.shortcuts import render
from django.views import generic

# Create your views here.
class HomeView(generic.TemplateView):
	template_name = "cm_main/base.html"