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
		if settings.HOME_LOGO:
			home_logo = settings.HOME_LOGO
		else:
			stat = static('images/cousinsmatter.jpg')
			home_logo = urlunparse(stat)
			logger.warn(home_logo)
		return {
			"home_title": settings.HOME_TITLE,
			"home_content": settings.HOME_CONTENT_SIGNED if self.request.user.is_authenticated else settings.HOME_CONTENT_UNSIGNED,
			"home_logo": home_logo,
			"site_copyright": settings.SITE_COPYRIGHT
		}