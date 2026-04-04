from .base import *  # noqa: F403, F405
from . import base

# Use a dummy secret key if none is provided in the environment/dotenv file
SECRET_KEY = env.str("SECRET_KEY", "dummy-secret-key-for-devtests")
SECRET_KEY_FALLBACKS = []

# Default domain and port for local development and testing
if getattr(base, "SITE_DOMAIN", None) is None:
  SITE_DOMAIN = "localhost"
  SITE_PORT = 8000

# Django Q2 settings: synchronous by default for easier debugging and testing
Q_CLUSTER["sync"] = env.bool("Q_SYNC", True)

# Default database host
DATABASES["default"]["HOST"] = env.str("POSTGRES_HOST", default="localhost")

# Default redis host
CHANNEL_LAYERS["default"]["CONFIG"]["hosts"] = [
  (
    env.str("REDIS_HOST", default="localhost"),
    env.int("REDIS_PORT", default=6379),
  )
]
