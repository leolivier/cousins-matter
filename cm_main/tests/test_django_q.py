from functools import wraps
from django_q.conf import Conf


class _DjangoQSwitcher:
  def __init__(self):
    self._saved = {}

  def enable(self):
    self._saved["SYNC"] = Conf.SYNC
    self._saved["TESTING"] = Conf.TESTING
    Conf.SYNC = True
    Conf.TESTING = True

  def disable(self):
    # restore even if exceptions have occurred
    Conf.SYNC = self._saved.get("SYNC", Conf.SYNC)
    Conf.TESTING = self._saved.get("TESTING", Conf.TESTING)
    self._saved.clear()


def django_q_sync_class(cls):
  """
  Decorator for test classes. For each method whose name starts with 'test'
  it envelops the call to activate django-q sync before execution and restore it afterwards.
  Does not replace setUp/tearDown.
  """
  switcher = _DjangoQSwitcher()

  def _wrap_test_method(method):
    @wraps(method)
    def _wrapped(self, *args, **kwargs):
      switcher.enable()
      try:
        return method(self, *args, **kwargs)
      finally:
        switcher.disable()

    return _wrapped

  for attr_name, attr_value in list(vars(cls).items()):
    if callable(attr_value) and attr_name.startswith("test"):
      setattr(cls, attr_name, _wrap_test_method(attr_value))

  return cls


def async_django_q_sync_class(cls):
  """
  Decorator for test classes. For each method whose name starts with 'test'
  it envelops the call to activate django-q sync before execution and restore it afterwards.
  Does not replace setUp/tearDown.
  """
  switcher = _DjangoQSwitcher()

  def _wrap_test_method(method):
    @wraps(method)
    async def _wrapped(self, *args, **kwargs):
      switcher.enable()
      try:
        return await method(self, *args, **kwargs)
      finally:
        switcher.disable()

    return _wrapped

  for attr_name, attr_value in list(vars(cls).items()):
    if callable(attr_value) and attr_name.startswith("test"):
      setattr(cls, attr_name, _wrap_test_method(attr_value))

  return cls
