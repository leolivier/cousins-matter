
class TestDjangoQMixin():
  def setUp(self):
    # override the django-q settings to make the tasks run synchronously
    super().setUp()
    from django_q.conf import Conf
    self.old_sync = Conf.SYNC
    self.old_testing = Conf.TESTING
    Conf.SYNC = True
    Conf.TESTING = True

  def tearDown(self):
    super().tearDown()
    # restore the django-q settings
    from django_q.conf import Conf
    Conf.SYNC = self.old_sync
    Conf.TESTING = self.old_testing
