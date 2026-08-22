"""
Decorators for views based on HTTP headers.
"""

import os
import shutil

from contextlib import contextmanager

from functools import wraps

from inspect import iscoroutinefunction
from django.conf import settings
from django.core.files.storage import default_storage

from django.http import HttpResponseBadRequest
from django.middleware.http import ConditionalGetMiddleware
from django.utils.decorators import decorator_from_middleware
from django.utils.log import log_response

from core.context_processors import override_settings

conditional_page = decorator_from_middleware(ConditionalGetMiddleware)


def require_htmx():
  """
  Decorator to make a view only accept HTMX requests. Usage::

      @require_httpx
      def my_view(request):
          # I can assume now that only HTMX requests make it this far
          # ...
  """

  def decorator(func):
    if iscoroutinefunction(func):

      @wraps(func)
      async def inner(request, *args, **kwargs):
        if not request.htmx:
          response = HttpResponseBadRequest("This view requires an HTMX request")
          log_response(
            "This view requires an HTMX request",
            response=response,
            request=request,
          )
          return response
        return await func(request, *args, **kwargs)

    else:

      @wraps(func)
      def inner(request, *args, **kwargs):
        if not request.htmx:
          response = HttpResponseBadRequest("This view requires an HTMX request")
          log_response(
            "This view requires an HTMX request",
            response=response,
            request=request,
          )
          return response
        return func(request, *args, **kwargs)

    return inner

  return decorator


@contextmanager
def set_test_media_root(test_file):
  """
  Context manager to set the MEDIA_ROOT to a temporary directory
  within the test file's directory. This is useful for tests that
  need to write files to the media directory. The temporary
  directory is automatically deleted after the test is complete.

  Args:
      test_file: The current test file.

  Yields:
      None
  """
  test_file = os.path.relpath(test_file, settings.BASE_DIR)
  # test_media_root = os.path.join(os.path.dirname(test_file), "media")
  # os.makedirs(test_media_root, exist_ok=True)
  submedia_reltestdir = "test_cfyguihjknmlnjbhg"
  test_media_root = os.path.join(settings.MEDIA_REL, submedia_reltestdir)
  dst = default_storage
  if "location" in dst.__dict__:
    old_storage_location = dst.location
  try:
    with override_settings(MEDIA_ROOT=test_media_root):
      if "location" in dst.__dict__:
        dst.location = test_media_root
      yield
  finally:
    # storage_rmtree(dst, submedia_reltestdir)
    if "location" in dst.__dict__:
      dst.location = old_storage_location
    if os.path.isdir(test_media_root):
      shutil.rmtree(test_media_root)


def test_media_root_decorator(test_file):
  """
  Decorator that sets the MEDIA_ROOT to a temporary directory
  within the test file's directory during the test. This is useful
  for tests that need to write files to the media directory. The
  temporary directory is automatically deleted after the test is
  complete.
  """

  def decorator(cls):
    orig_setUp = cls.setUp
    orig_tearDown = cls.tearDown

    def setUp(self, *args, **kwargs):
      self.test_media_root_context = set_test_media_root(test_file)
      self.test_media_root_context.__enter__()
      orig_setUp(self, *args, **kwargs)

    def tearDown(self, *args, **kwargs):
      orig_tearDown(self, *args, **kwargs)
      self.test_media_root_context.__exit__(None, None, None)

    cls.setUp = setUp
    cls.tearDown = tearDown
    return cls

  return decorator


@contextmanager
def temporary_log_level(logger, level):
  original_level = logger.level
  logger.setLevel(level)
  try:
    yield
  finally:
    logger.setLevel(original_level)
