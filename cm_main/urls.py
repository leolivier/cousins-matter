"""
URL configuration for cousinsmatter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.utils import timezone
from django.urls import path
from django.views.i18n import JavaScriptCatalog
from django.views.decorators.http import last_modified
from .views import views_general, views_contact, views_stats

app_name = "cm_main"
last_modified_date = timezone.now()
urlpatterns = [
  path("", views_general.HomeView.as_view(), name="Home"),
  path("contact/", views_contact.ContactView.as_view(), name="contact"),
  path("about/", views_stats.statistics, name="about"),
  path(
    "jsi18n/cm_main/<str:lang>",  # JS Catalog will be reloaded only at server restart, caching by language
    last_modified(lambda req, **kw: last_modified_date)(JavaScriptCatalog.as_view(packages=["cm_main"])),
    name="javascript-catalog",
  ),
]
