"""URL routes for the multi-tenant product feature.

Only mounted when MULTI_TENANT_ENABLED is on (see cousinsmatter/urls.py).
"""

from django.urls import path

from .views import views_manage, views_settings, views_signup

app_name = "tenants"

urlpatterns = [
  path("signup/", views_signup.FamilySignupView.as_view(), name="family_signup"),
  path("settings/", views_settings.TenantSettingsUpdateView.as_view(), name="settings"),
  path("", views_manage.TenantListView.as_view(), name="list"),
  path("create/", views_manage.TenantCreateView.as_view(), name="create"),
  path("<slug:slug>/toggle-active/", views_manage.TenantToggleActiveView.as_view(), name="toggle_active"),
  path("<slug:slug>/delete/", views_manage.TenantDeleteView.as_view(), name="delete"),
]
