"""URL routes for the SaaS flow. Only mounted when SAAS_LANDING_ENABLED is on."""

from django.urls import path

from .views import views_onboarding, views_signup, views_validate

app_name = "saas"

urlpatterns = [
  path("signup/", views_signup.SignupRequestView.as_view(), name="signup"),
  path("signup/sent/", views_signup.SignupSentView.as_view(), name="signup_sent"),
  path("welcome/", views_validate.WelcomeView.as_view(), name="welcome"),
  path(
    "validate/<str:encoded>/<str:token>/",
    views_validate.TenantValidateView.as_view(),
    name="validate",
  ),
  path("onboarding/dismiss/", views_onboarding.dismiss_onboarding, name="onboarding_dismiss"),
]
