from typing import Any
from django.views import generic
from cousinsmatter import settings
from django.templatetags.static import static
from urllib.parse import urlunparse
import logging

logger = logging.getLogger(__name__)

class HomeView(generic.TemplateView):
	template_name = "cm_main/base.html"
	def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
		return {
			"home_title": settings.HOME_TITLE,
			"home_content": settings.HOME_CONTENT_SIGNED if self.request.user.is_authenticated else settings.HOME_CONTENT_UNSIGNED,
			"home_logo": urlunparse(settings.HOME_LOGO) if settings.HOME_LOGO else None,
			"site_copyright": settings.SITE_COPYRIGHT
		}