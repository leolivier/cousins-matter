"""Shared test helpers for the saas app."""

from django.conf import settings


def skip_if_saas_off(testcase):
  """/saas/ URLs only exist when the SaaS flag is on at URLconf import."""
  if not settings.SAAS_LANDING_ENABLED:
    testcase.skipTest("SAAS_LANDING_ENABLED off in environment")
