from django.db import models
from django.utils.translation import gettext_lazy as _
from cousinsmatter import settings 
import os

class CousinsMatterParameters(models.Model):
  home_title = models.CharField(_("Home title"), max_length=128, 
                                default=_('Cousins Matter!'))
  home_content = models.TextField(_("Home content", 
                                    default=_("No home content yet, please go to <a href='/admin'>admin site</a> and create one.")))
  home_logo = models.ImageField(_("Home logo"), 
                                default=os.path.join(settings.STATIC_URL, 'images', 'cousinsmatter.jpg'))
