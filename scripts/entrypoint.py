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
from django.core.management import call_command, CommandError
from .create_superuser import create_superuser

logger = logging.getLogger(__name__)
INIT_IN_PROGRESS_DIR = Path("/app/data/.init_in_progress")  # lock file (mkdir target)


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
      logger.info(f"\nReceived signal {signal.Signals(signum).name}, cleaning up...")
    else:
      logger.info(f"\nReceived signal {signum}, cleaning up...")
  except Exception:
    logger.info(f"\nReceived signal {signum}, cleaning up...")
  cleanup()
  sys.exit(1)


def wait_init_and_exec(wait_time=10):
  """Wait for initialization to complete or timeout and exec CMD if no timeout"""
  logger.debug(f"Waiting (max {wait_time} seconds)...")

  for i in range(1, wait_time + 1):
    if not INIT_IN_PROGRESS_DIR.exists():
      logger.debug("Initialization completed by another process.")
      exec_docker_cmd()
    time.sleep(1)

  logger.error(f"Init not finished in {wait_time} seconds, please remove {INIT_IN_PROGRESS_DIR} manually. Exiting...")
  sys.exit(1)


def acquire_lock():
  """
  Try to acquire initialization leadership via atomic mkdir creation.
        If mkdir succeeds, we are the leader, otherwise, we wait for the lock to be released and exit.
        """
  try:
    INIT_IN_PROGRESS_DIR.mkdir(parents=True, exist_ok=False)
    logger.debug("Initialization lock acquired.")
  except FileExistsError:
    logger.debug("Failed to acquire lock: Another container is already initializing the environment.")
    wait_init_and_exec(20)


def first_run_init():
    """Check if this is first run by trying to create avatars directory
    if first run, create other needed directories and files
    """
    avatars_dir = Path("/app/media/avatars")
    try:
      avatars_dir.mkdir(parents=True, exist_ok=False)
      # First run setup
      logger.debug("Setting up directories for first run...")
      media_public = Path("/app/media/public")
      media_public.mkdir(parents=True, exist_ok=True)
      theme_css = media_public / "theme.css"
      theme_css.touch()
      logger.info("Created media subdirectories and theme.css file.")
      return True
    except FileExistsError:
      logger.debug("This is not the first run. Skipping first run init...")
      return False


def run_migrations():
  """Run migrations"""
  try:
    logger.info("Running migrations...")
    call_command("migrate", no_input=True, interactive=False)
  except CommandError as e:
    logger.error(f"Error running migrations: {e}")
    sys.exit(1)


def run_collectstatic():
  """Run collectstatic"""
  try:
    logger.info("Collecting static files...")
    call_command("collectstatic", no_input=True, interactive=False)
  except CommandError as e:
    logger.error(f"Error running collectstatic: {e}")
    sys.exit(1)


def run_check():
  """Run check"""
  try:
    logger.info("Running checks...")
    call_command("check", deploy=True)
  except CommandError as e:
    logger.error(f"Error running checks: {e}")
    sys.exit(1)


def run_create_superuser(env: environ.Env):
  """Run create superuser"""
  try:
    logger.info("Creating superuser...")
    create_superuser(env)
  except CommandError as e:
    logger.error(f"Error creating superuser: {e}")
    sys.exit(1)


def initialize_environment(env: environ.Env):
  """Main initialization logic"""

  # Initialize Django
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
  django.setup()

  # Check SECRET_KEY
  secret_key = env.str("SECRET_KEY", "")
  if not secret_key:
    raise InitException("Error: SECRET_KEY is not set in the .env file.", 3)

  # Set up signal handlers for cleanup
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGHUP, signal_handler)
  signal.signal(signal.SIGQUIT, signal_handler)

  # Try to acquire lock using mkdir
  acquire_lock()

  try:
    first_run = first_run_init()
    run_migrations()
    run_collectstatic()
    run_check()
    if first_run:
      run_create_superuser(env)

    logger.info("Environment is ready...")

  finally:
    # Cleanup is handled by signal handlers and this ensures cleanup on normal exit
    cleanup()

  logger.info("Environment is ready...")


def exec_docker_cmd():
  # After initialization, exec the provided command (like `exec "$@"`)
  args = sys.argv[1:]
  if not args:
    logger.error("No command provided to exec. Exiting.")
    sys.exit(2)

  logger.info("starting:", " ".join(args))
  # Replace current process with the target command
  try:
    os.execvp(args[0], args)
  except FileNotFoundError:
    logger.error(f"Command not found: {args[0]}")
    sys.exit(127)


def main():
    """Main entry point"""
    try:
        env_file = Path("/app/.env")
        # Check current working directory
        if os.getcwd() != '/app':
          raise InitException("""The container is inconsistent: PWD is not set to /app.
Please make sure you are in the project directory before running this script.""", 1)

        # Check .env file exists and is readable
        if not env_file.exists() or not env_file.is_file():
          raise InitException("""
The .env file is missing or not readable.
Please download .env.example from github latest release, rename it to .env, and fill it with the right data.
Then use --force-recreate option with 'docker compose up' to recreate the container.""", 2)
        # load keys from .env
        env = environ.Env(
            # set casting, default value
            DEBUG=(bool, False)
        )
        env.read_env(env_file, overwrite=True)

        # Enable debug output (equivalent to 'set -x' in bash)
        if env.bool('DEBUG', False):
            logging.basicConfig(level=logging.DEBUG)

        initialize_environment(env)
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
