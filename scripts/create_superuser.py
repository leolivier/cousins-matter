#!/usr/bin/env python3
"""
Create a Django superuser based on .env variables. Must be run in the cousins-matter container

Usage:
  - As a script: `docker exec cousins-matter python scripts/create_superuser.py`
  - As a package from Python: `from scripts.create_superuser import create_superuser_from_env; create_superuser_from_env()`
"""

import django
import environ
import logging
import os
import sys
from django.conf import settings

logger = logging.getLogger(__name__)


def error(code: int, *msg: str) -> None:
  """Will print the given message to stderr and exit with the given code"""
  print(" ".join(str(m) for m in msg), file=sys.stderr)
  sys.exit(code)


def create_superuser_from_env():
  """Create a Django superuser based on environment variables stored in .env file."""
  from members.models import Member

  env = environ.Env()
  env.read_env(settings.BASE_DIR / ".env", overwrite=True)
  username = env.str("ADMIN")
  email = env.str("ADMIN_EMAIL")
  password = env.str("ADMIN_PASSWORD")
  first_name = env.str("ADMIN_FIRSTNAME", default="Cousins")
  last_name = env.str("ADMIN_LASTNAME", default="Matter")
  birthdate = env.str("ADMIN_BIRTHDATE", default="2000-01-01")
  logger.info("Creating superuser...")
  try:
    Member.objects.create_superuser(
      username=username,
      email=email,
      password=password,
      first_name=first_name,
      last_name=last_name,
      birthdate=birthdate,
    )
  except Exception as e:
    error(1, f"Superuser creation failed: {e}")

  try:
    su = Member.objects.get(username=username)
    if not su.is_superuser:
      error(
        2,
        f"Superuser creation failed: user {username} was created but is not a superuser",
      )
  except Member.DoesNotExist:
    error(3, f"Superuser creation failed: user {username} does not exist")

  logger.info("Superuser created successfully")


if __name__ == "__main__":
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cousinsmatter.settings")
  django.setup()
  create_superuser_from_env()
