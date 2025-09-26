#!/usr/bin/env python3
"""
Create a Django superuser based on environment variables.

Usage:
  - As a script: `python scripts/create_superuser.py`
  - As a package from Python: `from scripts.create_superuser import create_superuser; create_superuser(env)`
    env must must be an instance of environ.Env
"""
import django
import environ
import os
import sys
from pathlib import Path


def create_superuser(env):
    """Create a Django superuser based on environment variables stored in .env file."""
    from members.models import Member
    Member.objects.create_superuser(
      username=env.str('ADMIN'),
      email=env.str('ADMIN_EMAIL'),
      password=env.str('ADMIN_PASSWORD'),
      first_name=env.str('ADMIN_FIRSTNAME', default="Cousins"),
      last_name=env.str('ADMIN_LASTNAME', default="Matter"),
      birthdate=env.str('ADMIN_BIRTHDATE', default="2000-01-01"))

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
    # is it needed to read the env file or the setdefault above is enough?
    env = environ.Env()
    env.read_env(BASE_DIR / ".env", overwrite=True)
    django.setup()
    create_superuser(env)
    sys.exit(0)
