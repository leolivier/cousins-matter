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

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

# from django.utils.translation import gettext_lazy as _
 
# admin.site.index_title = _('My Index Title')
# admin.site.site_header = _('My Site Administration')
# admin.site.site_title = _('My Site Management')

urlpatterns = [
    path("", include("cm_main.urls")),
    path("accounts/", include("accounts.urls")),
    path("members/", include("members.urls")),
    path("news/", include("news.urls")),
    path("galleries/", include("galleries.urls")),
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
    #path("ckeditor/", include("ckeditor_uploader.urls")),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='reset_password'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
	path('password-reset/completed/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('verification/', include('verify_email.urls')),	
    path("robots.txt", TemplateView.as_view(template_name="cm_main/robots.txt", content_type="text/plain")),
	path('captcha/', include('captcha.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
