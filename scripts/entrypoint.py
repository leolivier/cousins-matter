#!/usr/bin/env python3
"""
Initializes the Django application environment and then execs the provided command.

Behavior mirrors old scripts/entrypoint.sh:
- Ensure only one container performs initialization via an atomic mkdir lock
- Validate current working directory and .env
- Verify SECRET_KEY is set
- On first run, create media directories and theme.css, then create superuser
- Run migrate, collectstatic, and check --deploy
- Finally exec the container CMD/args
"""

import django
import environ
import logging
import os
import redis
import signal
import sys
import time
from pathlib import Path
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings

# from cousinsmatter import settings as cousinsmatter_defaults
from django.core.management import call_command, CommandError
from .create_superuser import create_superuser_from_env, has_superuser

logger = logging.getLogger(f"{__name__}/{sys.argv[1]}")

# Locking management
INIT_LOCK_KEY = "CM__init_lock__"
FIRST_RUN_LOCK_KEY = "CM__first_run_lock__"
LOCK_TIMEOUT_SECONDS = 60  # Safety
REDIS_SINGLETON = None  # used only in get_redis()


def get_redis():
  global REDIS_SINGLETON
  if REDIS_SINGLETON is None:
    REDIS_SINGLETON = redis.Redis(
      host=settings.Q_CLUSTER["redis"]["host"],
      port=settings.Q_CLUSTER["redis"]["port"],
    )
  return REDIS_SINGLETON


class InitException(Exception):
  def __init__(self, message, code):
    self.message = message
    self.code = code
    super().__init__(message)


def signal_handler(signum, frame):
  """Handle termination signals by cleaning up lock and exiting."""
  try:
    sig_name = getattr(signal, "Signals", None)
    if sig_name:
      logger.warn(f"\nReceived signal {signal.Signals(signum).name}, cleaning up...")
    else:
      logger.warn(f"\nReceived signal {signum}, cleaning up...")
  except Exception:
    logger.warn(f"\nReceived signal {signum}, cleaning up...")

  release_lock()
  sys.exit(1)


def acquire_lock():
  """
  Tries to acquire initialization leadership via a lock in Redis.
  Returns True if the lock was acquired, False if it was not.
  """
  # Attempts to set a lock (SETNX) with an expiration (ex)
  # nx=True -> Only create the key if it does not exist
  # ex=60 -> The key will expire after LOCK_TIMEOUT_SECONDS seconds (to prevent permanent lockouts).
  if get_redis().set(INIT_LOCK_KEY, "in_progress", nx=True, ex=LOCK_TIMEOUT_SECONDS):
    # We got the lock!
    logger.info("Lock acquired. Running init tasks...")
    return True
  else:
    # The lock is already taken.
    logger.info("Another process is running init. Waiting...")
    return False


def release_lock():
  get_redis().delete(INIT_LOCK_KEY)
  logger.info("Init finished. Lock released.")


def wait_for_lock(wait_time=20):
  """Wait for initialization to complete or timeout"""
  logger.info(f"Waiting (max {wait_time} seconds)...")

  for i in range(wait_time):
    if not get_redis().exists(INIT_LOCK_KEY):
      logger.info("Init finished by another process. Starting.")
      return True  # It's okay, the init is done.
    time.sleep(1)

  logger.error(f"Init not finished in {wait_time}s. Exiting.")
  sys.exit(1)


def check_db_connection():
  # Tries to establish a connection with Django's default settings
  db_conn = connections["default"]
  db_conn.cursor()
  return True


def wait_for_db():
  MAX_RETRIES = 60
  RETRY_DELAY = 0.5

  logger.info("Waiting for database connection...")

  for i in range(MAX_RETRIES):
    try:
      # Try to connect to the database
      check_db_connection()
      # try to ping redis
      get_redis().ping()
      logger.info("Postgres and Redis are ready!")
      return
    except OperationalError as e:
      if i < MAX_RETRIES - 1:
        logger.debug(f"Postgres and/or Redis unavailable ({i + 1}/{MAX_RETRIES}), waiting {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
      else:
        logger.error(f"Error: Postgres and/or Redis connection failed after {MAX_RETRIES * RETRY_DELAY} seconds.")
        logger.exception("Last error:", exc_info=e)
        raise InitException("Error: cannot connect to database.", 1)


def run_migrations():
  """Run Django migrations"""
  try:
    logger.info("Running Django migrations...")
    call_command("migrate", no_input=True, interactive=False)
  except CommandError as e:
    logger.error(f"Error running Django migrations: {e}")
    sys.exit(1)


def run_collectstatic():
  """Run Django collectstatic"""
  try:
    logger.info("Collecting static files...")
    call_command("collectstatic", no_input=True, interactive=False)
  except CommandError as e:
    logger.error(f"Error running Django collectstatic: {e}")
    sys.exit(1)


def run_check_deploy():
  """Run check"""
  try:
    logger.info("Running Django deployment checks...")
    call_command("check", deploy=True)
  except CommandError as e:
    logger.error(f"Error running Django deployment checks: {e}")
    sys.exit(1)


def run_create_superuser():
  """Create superuser using environment variables"""
  try:
    if not has_superuser():
      logger.info("Creating superuser...")
      create_superuser_from_env()
    else:
      logger.info("Superuser already exists.")
  except CommandError as e:
    logger.error(f"Error creating superuser: {e}")
    sys.exit(1)


def set_logger_level(debug: bool):
  """Set logger level based on debug setting"""
  level = logging.DEBUG if debug else logging.INFO
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  logger.setLevel(level)
  if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
  else:
    for h in logger.handlers:
      h.setLevel(level)
      h.setFormatter(formatter)
  # print("effective logger level:", logger.getEffectiveLevel())


def initialize_environment():
  """Main initialization logic"""

  set_logger_level(settings.DEBUG)
  # Check SECRET_KEY
  if not settings.SECRET_KEY:
    raise InitException("Error: SECRET_KEY is not set in the .env file.", 3)

  # Set up signal handlers for cleanup
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGHUP, signal_handler)
  signal.signal(signal.SIGQUIT, signal_handler)

  wait_for_db()
  if acquire_lock():  # we got the lock, we can do the init
    try:
      run_migrations()
      run_collectstatic()
      run_check_deploy()
      run_create_superuser()

      logger.info("Environment is ready...")

    finally:
      # Release the acquired lock
      release_lock()

  else:
    wait_for_lock(20)


def exec_docker_cmd():
  # After initialization, exec the provided command (like `exec "$@"`)
  args = sys.argv[1:]
  if not args:
    logger.error("No command provided to exec. Exiting.")
    sys.exit(2)

  logger.info(f"starting: {' '.join(args)}")
  # Replace current process with the target command
  try:
    os.execvp(args[0], args)
  except FileNotFoundError:
    logger.error(f"Command not found: {args[0]}")
    sys.exit(127)


def check_environment() -> environ.Env:
  """Check environment variables"""
  # Check current working directory
  if Path.cwd() != settings.BASE_DIR:
    raise InitException(
      f"""The container is inconsistent: PWD is not set to {settings.BASE_DIR}.
Please make sure you are in the project directory before running this script.""",
      1,
    )
  env_file = settings.BASE_DIR / ".env"
  # this should be checked in settings.py
  if not env_file.exists() or not env_file.is_file():
    raise InitException(
      """
The .env file is missing or not readable.
Please download .env.example from github latest release, rename it to .env, and fill it with the right data.
Then use --force-recreate option with 'docker compose up' to recreate the container.""",
      2,
    )


def main():
  """Main entry point"""

  try:
    # Initialize Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cousinsmatter.settings")
    # settings.configure(default_settings=cousinsmatter_defaults, DEBUG=True)
    django.setup()
    check_environment()
    initialize_environment()
    exec_docker_cmd()
  except InitException as e:
    logger.error(f"Error during initialization: {e.message}")
    sys.exit(e.code)
  except Exception as e:
    logger.error(f"Unexpected error during initialization: {e}")
    sys.exit(1)
  finally:
    release_lock()


if __name__ == "__main__":
  main()
