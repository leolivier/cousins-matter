from typing import Any
from django.shortcuts import render
from django.views import generic
from . import models

class HomeView(generic.TemplateView):
	template_name = "cm_main/base.html"
	def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
		params = models.CousinsMatterParameters.objects.first()
		return params.__dict__ if params else {}