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
from django.core.management import call_command


def create_superuser(env):
    """Create a Django superuser based on environment variables stored in .env file."""
    call_command("createsuperuser",
                 interactive=False,
                 password=env.str('ADMIN_PASSWORD'),
                 username=env.str('ADMIN'),
                 email=env.str('ADMIN_EMAIL'),
                 first_name=env.str('ADMIN_FIRSTNAME', default="Cousins"),
                 last_name=env.str('ADMIN_LASTNAME', default="Matter"))


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
    env = environ.Env()
    env.read_env("/app/.env", overwrite=True)
    django.setup()
    create_superuser(env)
    sys.exit(0)
