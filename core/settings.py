import os

envt = os.getenv("ENVIRONMENT", "production")
match envt:
  case "development":
    from config.settings.development import *  # noqa: F403, F405
  case "production":
    from config.settings.production import *  # noqa: F403, F405
  case "test":
    from config.settings.local_test import *  # noqa: F403, F405
  case "docker-devt":
    from config.settings.docker_devt import *  # noqa: F403, F405
  case "docker-test":
    from config.settings.docker_test import *  # noqa: F403, F405
  case _:
    raise ValueError(f"Unknown environment: {envt}")

print(f"Starting Environment: {envt}")
