from django_htmx.http import (
  HttpResponseClientRedirect,
  HttpResponseClientRefresh,
  trigger_client_event,
)


def htmx_refresh():
  return HttpResponseClientRefresh()


def htmx_redirect(url):
  return HttpResponseClientRedirect(url)


def htmx_trigger_event(response, event_name, params=None):
  return trigger_client_event(response, event_name, params)
