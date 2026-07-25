"""Non-regression tests for the CHANNEL_LAYERS / channels-redis configuration.

History: channels-redis blocks on BZPOPMIN (brpop_timeout=5s) to wait for
messages. redis-py's DEFAULT_SOCKET_TIMEOUT is 5s, so any non-None socket_timeout
races with that BZPOPMIN and aborts every idle receive with
"Timeout reading from <host>:6379". The protection against genuinely dead
connections is health_check_interval (periodic ping), NOT socket_timeout.

These invariants must hold in every environment (base/dev_base/docker_devt/
docker_test/production all derive from the same base.py dict-format config).
"""

from django.conf import settings
from django.test import SimpleTestCase


class ChannelsRedisConfigTests(SimpleTestCase):
  def test_hosts_uses_dict_format(self):
    """hosts entries must be dicts, not plain (host, port) tuples — otherwise
    all connection options (health_check_interval, keepalive, retry) are dropped."""
    hosts = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"]
    self.assertTrue(hosts, "CHANNEL_LAYERS hosts list is empty")
    self.assertIsInstance(
      hosts[0],
      dict,
      "hosts[0] must be a dict; a plain (host, port) tuple drops all connection options",
    )

  def test_socket_timeout_is_none(self):
    """socket_timeout MUST be explicitly None. A missing key falls back to
    redis-py's DEFAULT_SOCKET_TIMEOUT (5s), which races with BZPOPMIN and breaks
    message reception — so we assert against a sentinel default of 5."""
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    self.assertIsNone(
      host.get("socket_timeout", 5),
      "socket_timeout must be explicitly None; omitting the key keeps the 5s "
      "default which races with channels-redis BZPOPMIN (brpop_timeout=5s).",
    )

  def test_health_check_interval_is_set(self):
    """health_check_interval must be > 0: with socket_timeout=None, this is the
    only mechanism that detects and recovers dead connections."""
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0]
    self.assertGreater(host.get("health_check_interval", 0), 0)
