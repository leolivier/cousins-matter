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
import signal
import sys
import time
from pathlib import Path
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
# from cousinsmatter import settings as cousinsmatter_defaults
from django.core.management import call_command, CommandError
from .create_superuser import create_superuser_from_env

logger = logging.getLogger(f"{__name__}/{sys.argv[1]}")
INIT_IN_PROGRESS_DIR = None  # set in acquire_lock


class InitException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(message)


def cleanup():
  """Remove lock dir if present."""
  try:
      if INIT_IN_PROGRESS_DIR.exists():
          INIT_IN_PROGRESS_DIR.rmdir()
          logger.debug(f"Removed lock {INIT_IN_PROGRESS_DIR}")
  except Exception as e:
      logger.error(f"Warning: Could not remove {INIT_IN_PROGRESS_DIR}: {e}")


def signal_handler(signum, frame):
  """Handle termination signals by cleaning up lock and exiting."""
  try:
    sig_name = getattr(signal, 'Signals', None)
    if sig_name:
      logger.warn(f"\nReceived signal {signal.Signals(signum).name}, cleaning up...")
    else:
      logger.warn(f"\nReceived signal {signum}, cleaning up...")
  except Exception:
    logger.warn(f"\nReceived signal {signum}, cleaning up...")
  cleanup()
  sys.exit(1)


def wait_init_and_exec(wait_time=10):
  """Wait for initialization to complete or timeout and exec CMD if no timeout"""
  logger.info(f"Waiting (max {wait_time} seconds)...")

  for i in range(1, wait_time + 1):
    if not INIT_IN_PROGRESS_DIR.exists():
      logger.info("Initialization completed by another process.")
      exec_docker_cmd()
    time.sleep(1)

  logger.error(f"Init not finished in {wait_time} seconds, please remove {INIT_IN_PROGRESS_DIR} manually. Exiting...")
  sys.exit(1)


def acquire_lock():
  """
  Try to acquire initialization leadership via atomic mkdir creation.
        If mkdir succeeds, we are the leader, otherwise, we wait for the lock to be released and exit.
        """
  global INIT_IN_PROGRESS_DIR
  try:
    INIT_IN_PROGRESS_DIR = settings.BASE_DIR / "data/.init_in_progress"  # lock dir
    INIT_IN_PROGRESS_DIR.mkdir()
    logger.info("Initialization lock acquired.")
  except FileExistsError:
    logger.info("Failed to acquire lock: Another container is already initializing the environment.")
    wait_init_and_exec(20)
  except FileNotFoundError as e:
    logger.exception(f"{settings.BASE_DIR}/data does not exist. It should have been created by docker_install.sh",
                     exc_info=e)
    sys.exit(1)


def first_run_init():
    """Check if this is first run by trying to create avatars directory
    if first run, create other needed directories and files
    """
    first_run_lock_dir = settings.BASE_DIR / "data/.first_run_done"  # lock dir
    try:
      # will raise FileExistsError if it already exists
      # and FileNotFoundError if MEDIA_ROOT does not exist
      first_run_lock_dir.mkdir()

      # First run setup
      logger.debug("Setting up directories for first run...")
      avatars_dir = settings.MEDIA_ROOT / settings.AVATARS_DIR
      avatars_dir.mkdir(exist_ok=True)
      settings.PUBLIC_MEDIA_ROOT.mkdir(exist_ok=True)
      theme_css = settings.PUBLIC_MEDIA_ROOT / "theme.css"
      theme_css.touch()
      logger.info("Created media subdirectories and theme.css file.")
      return True
    except FileExistsError:
      logger.info("This is not the first run. Skipping first run init...")
      stats = first_run_lock_dir.stat()
      logger.info(f"First run lock directory {first_run_lock_dir} stats: {stats}")
      return False
    except FileNotFoundError as e:
      logger.exception("File not found", exc_info=e)
      sys.exit(1)


def check_db_connection():
  # Tries to establish a connection with Django's default settings
  db_conn = connections['default']
  db_conn.cursor()
  return True

def wait_for_db():
  MAX_RETRIES = 60
  RETRY_DELAY = 0.5

  logger.info('Waiting for database connection...')

  for i in range(MAX_RETRIES):
      try:
          # Try to connect to the database
          check_db_connection()
          logger.info('Database is ready!')
          return
      except OperationalError as e:
        if i < MAX_RETRIES - 1:
          logger.debug(f'Database unavailable ({i+1}/{MAX_RETRIES}), waiting {RETRY_DELAY} seconds...')
          time.sleep(RETRY_DELAY)
        else:
          logger.error(f'Error: Database connection failed after {MAX_RETRIES * RETRY_DELAY} seconds.')
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
    logger.info("Creating superuser...")
    create_superuser_from_env()
  except CommandError as e:
    logger.error(f"Error creating superuser: {e}")
    sys.exit(1)


def set_logger_level(debug: bool):
  """Set logger level based on debug setting"""
  level = logging.DEBUG if debug else logging.INFO
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

  # Try to acquire lock using mkdir
  acquire_lock()
  # will never come here if the lock is not acquired
  try:
    first_run = first_run_init()
    wait_for_db()  # here, or before acquire_lock() ?
    run_migrations()
    run_collectstatic()
    run_check_deploy()
    if first_run:
      run_create_superuser()

    logger.info("Environment is ready...")

  finally:
    # Cleanup is handled by signal handlers and this ensures cleanup on normal exit
    cleanup()


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
    raise InitException(f"""The container is inconsistent: PWD is not set to {settings.BASE_DIR}.
Please make sure you are in the project directory before running this script.""", 1)
  env_file = settings.BASE_DIR / ".env"
  # this should be checked in settings.py
  if not env_file.exists() or not env_file.is_file():
    raise InitException("""
The .env file is missing or not readable.
Please download .env.example from github latest release, rename it to .env, and fill it with the right data.
Then use --force-recreate option with 'docker compose up' to recreate the container.""", 2)


def main():
    """Main entry point"""

    try:
      # Initialize Django
      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
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
        cleanup()


if __name__ == "__main__":
    main()
