import os
from django.conf import settings

envt = os.getenv("ENVIRONMENT", "production")
match envt:
  case "development":
    from config.settings.development import *
  case "production":
    from config.settings.production import *
  case "test":
    from config.settings.test import *
  case "docker-devt":
    from config.settings.docker_devt import *
  case "docker-test":
    from config.settings.docker_test import *
  case _:
    raise ValueError(f"Unknown environment: {envt}")

print(f"Starting Environment: {envt}")
