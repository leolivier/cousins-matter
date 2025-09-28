#!/usr/bin/env python3

"""
A Python script to migrate Cousins Matter from v1 to v2.

It will:
- Check the directory looks like a Cousins Matter project and contains a data/db.sqlite3 file
- Fix permissions from old UID 5678 to 1000 using sudo
- Start Postgres with Docker and wait for readiness
- Run the migration profile to move from sqlite to postgres
- Download v2 files (docker-compose.yml, .env.example, scripts/rotate-secrets.sh) from GitHub
- Run the rotate secrets script

Usage:
  ./scripts/migrate_v1_v2.py [-q] [-d directory] [-b branch]

Notes:
- Requires python3, Docker and sudo available on the system.
- Network access is needed to fetch files from GitHub.
- Uses only Python standard library; no external Python packages are required.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from .utils import (
  verbose, error, set_verbose, run, require_docker, docker_logs,
  rotate_secrets, ON_RED, ON_WHITE, ON_GREEN, NC, download_github_files
)

# Repository to fetch v2 files from
GITHUB_REPO = "leolivier/cousins-matter"


def ensure_project_dir(directory: Path):
    make_sure = f"{ON_RED}Please make sure first you are in a cousins-matter directory before running this script{NC}"
    if not (directory / ".env").is_file():
        error(10, "No .env file found in the directory.", make_sure)
    if not (directory / "docker-compose.yml").is_file():
        error(11, "No docker-compose.yml file found in the directory.", make_sure)
    data_dir = directory / "data"
    if not data_dir.is_dir():
        error(12, "No data directory found in the directory.", make_sure)
    if not (data_dir / "db.sqlite3").is_file():
        error(13, "No db.sqlite3 file found in the data directory.", make_sure)


def fix_permissions():
  target_uid = 5678        # UID to search
  new_uid = 1000           # new owner UID
  new_gid = 1000           # new group GID
  for path in Path(".").rglob("*"):
    try:
      st = path.lstat()
    except FileNotFoundError:
      return
    except PermissionError:
      print(f"Permission denied (lstat): {path}", file=sys.stderr)
      return

    if st.st_uid == target_uid:
      try:
        path.chown(new_uid, new_gid)
      except PermissionError:
        print(f"Permission denied (chown): {path}", file=sys.stderr)
      except FileNotFoundError:
        pass


def wait_for_postgres_ready():
    """
    Waits until the postgres logs contain the readiness message twice
    (the first time is when the container starts, the second time is when the database is ready)
    """
    target = "database system is ready to accept connections"
    err_marker = "initdb: error:"

    verbose("Waiting for postgres to be ready", end="")

    while True:
        verbose("...", end="")
        time.sleep(5)
        logs = docker_logs("cousins-matter-postgres")
        ready_count = logs.count(target)
        if ready_count >= 2:
            verbose("")  # newline
            return
        if err_marker in logs:
            # Echo out the error lines to help users
            for line in logs.splitlines():
                if err_marker in line:
                    print(line)
            error(17, """Postgres failed to start, see error message above, try to fix it (usually it's a permission issue),
then rerun this script""")


def run_migration():

    # Start postgres and wait for readiness
    verbose("Starting postgres server...")
    run(["docker", "compose", "up", "-d", "postgres"], check=True)
    wait_for_postgres_ready()  # here, postgres should be ready and its named volume should be mounted
    verbose("Postgres is ready, starting migration...")

    try:
        # Run migration profile (will start pgloader)
        run(["docker", "compose", "--profile", "migrate", "up", "migrate"], check=True)
    except subprocess.CalledProcessError as e:
        error(16, f"""Migration failed, see error message, try to fix it (usually it's a password issue),
then rerun this script: {e}""")

    verbose("Migration done, removing pgloader container...")
    subprocess.run(["docker", "container", "rm", "cousins-matter-pgloader"], check=False)

    print(f"""
{ON_GREEN}Your database has now been migrated to postgres, you can start Cousins Matter with 'docker compose up -d'{NC}
{ON_RED}IMPORTANT:{NC}
{ON_WHITE}Don't remove the db.sqlite3 file until you have checked that the postgres database has been correctly
initialized.{NC}
Navigate in your site and check that all data is there.
{ON_RED}TIP:{NC} You can also have a look at the migration log in the table above and check that the number of migrated
rows is correct.
Look specifically at 'members_memeber' (the number of members), 'galleries_gallery' (the number of galleries),
'galleries_photo' (the number of photos), 'forum_post' (the number of forum posts), 'chat_chatroom' and 'chat_privatechatroom'
(the number of public and private chat rooms), 'polls_poll' (the number of polls), 'classified_ads_classifiedad' (the number
of classified ads), and 'troves_trove' (the number of \"treasures\") to make sure they are correct.
If everything is correct, you can remove the db.sqlite3 file.
As redis is now using a named volume, you can remove the redis data directory if you want to, and thus the whole data
directory which is not needed anymore.
""")


def download_v2_scripts(directory: Path, branch: str | None):
  files = [
    ("docker-compose.yml", directory / "docker-compose.yml"),
    (".env.example", directory / ".env.example"),
    ("scripts/rotate-secrets.sh", directory / "scripts" / "rotate-secrets.sh"),
  ]
  download_github_files(files, directory, branch)


def check_cm_is_down():
    try:
      result = run(["docker", "ps", "-a", "--filter", "name=cousins-matter", "--format", "json"],
                   check=True, capture_output=True, text=True)
      if result.returncode != 0:
        error(1, "Unable to check if cousins-matter is down")
      containers = json.loads(f'[{",".join(result.stdout.splitlines())}]')
      if not containers:
        return
      errors = []
      for container in containers:
        name = container.get("Names", "")
        state = container.get("State", "")
        status = container.get("Status", "")
        if name == "cousins-matter" or name == "cousins-matter-qcluster":
          match state:
            case "running":
              errors.append(f"""Cousins Matter is already running ({status}),
please stop it and remove the container before running this script""")
            case "exited":
              errors.append(f"""Cousins Matter is already stopped ({status})
but the container is still there, please remove it before running this script""")
            case _:
              errors.append(f"""Cousins Matter is in an unknown state ({state}),
please remove the container before running this script""")
    except subprocess.CalledProcessError as e:
      error(1, f"Unable to check if cousins-matter is down: {e}")
    if errors:
      error(1, "\n".join(errors))


def main(argv=None):

    parser = argparse.ArgumentParser(description="Migrate Cousins Matter from v1.x to v2")
    parser.add_argument("-q", action="store_true", help="quiet mode")
    parser.add_argument("-d", dest="directory", default=os.getcwd(),
                        help="installation directory (default: current directory)")
    parser.add_argument("-b", dest="branch", default=None, help="branch to use (default: latest release)")

    args = parser.parse_args(argv)

    directory = Path(args.directory).resolve()
    set_verbose(not args.q)
    branch = args.branch

    # check docker is installed
    require_docker()

    verbose(f"{ON_WHITE}Migrating Cousins Matter from v1.x to v2...{NC}")
    verbose(f"Checking if directory {directory} looks like a cousins-matter project...")

    if not directory.exists() or not directory.is_dir():
        error(1, f"Error: directory {directory} does not exist")

    os.chdir(directory)

    ensure_project_dir(directory)

    check_cm_is_down()

    # verbose(f"Fixing permissions...")
    # fix_permissions()

    verbose("Migrating database...")
    run_migration()

    verbose("Downloading v2 scripts...")
    download_v2_scripts(directory, branch=branch)

    verbose("Rotating secrets...")
    rotate_secrets()


if __name__ == "__main__":
    main()
