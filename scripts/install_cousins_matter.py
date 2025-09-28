#!/usr/bin/env python3

"""
Python rewrite of scripts/docker-install.sh using only the Python standard library.

Usage:
  ./scripts/docker_install.py [-q] [-e] [-d directory] [-b branch] [-n][-h]

Behavior:
- Requires sudo and docker installed (like the original script).
- If '-e' is NOT specified (normal install):
  - Default directory is './cousins-matter'. Directory must be empty.
  - Download docker-compose.yml, .env.example, nginx.conf and scripts/rotate-secrets.sh from GitHub
    (uses urllib; no curl/wget dependency).
  - If .env does not exist, create it from .env.example; otherwise print warnings (same spirit as bash script).
- If '-e' IS specified (env-only/CI case):
  - Default directory is current directory.
  - Require that the script is located in a 'scripts' directory (dev environment check) and that .env exists;
    otherwise display the warning block like the bash script.
- In all cases:
  - Rotate/generate SECRET_KEY using rotate_secrets.py via a pure-Python import (no shell/subprocess for this).
  - Generate POSTGRES_PASSWORD if missing.
  - Create data/, data/postgres/, media/, static/ with appropriate permissions.
  - For normal install (no -e): show guidance and open ${EDITOR:-editor} .env after a countdown.
"""

import argparse
import os
import string
import time
from pathlib import Path
from .utils import (
    run, require_docker, get_regex, generate_key, strip_quotes, error,
    verbose, set_verbose, read_env, write_env, download_github_files, ENV_PATH
)
from .rotate_secrets import rotate_secrets


ALLOWED_PG_PASS_CHARS = string.ascii_letters + string.digits + "./_*"


def ensure_empty_directory(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return
    # Check empty: any entry which is not scripts?
    if any(filter(lambda x: not x.is_dir() or x.name != "scripts", path.iterdir())):
        error(1, f"{path} is not empty, cousins-matter must be installed in an empty directory.")


def get_directory(create_environment_only: bool, directory: str | None):
    # Resolve directory based on -e
    cwd = Path.cwd()
    if create_environment_only:  # create environment only
        directory = Path(directory or cwd).resolve()
        # Ensure we're running from scripts dir
        script_dir_name = Path(__file__).resolve().parent.name
        if script_dir_name != "scripts":
            error(1, "this script should be run from the scripts directory if -e selected. Are you in a devt environment?")
    else:
        directory = Path(directory or (cwd / "cousins-matter")).resolve()

    try:
        directory.mkdir(parents=True, exist_ok=False)
        verbose(f"directory {directory} does not exist, creating it...")
    except FileExistsError:
        verbose(f"directory {directory} already exists.")

    os.chdir(directory)

    if create_environment_only:
        # ensure .env exists; if not, print warning
        if not ENV_PATH.exists():
            print("###########################################################################################")
            print("# WARNING! '-e' param was provided and skipped dowloading .env.example. However, .env     #")
            print("# does not exist in this directory. Please check .env.example, .env.old if it exists, and #")
            print("# create a .env file to make sure all required variables are present.                     #")
            print("###########################################################################################")
    else:
        # Normal install: ensure directory is empty and move .env to .env.old if it exists
        ensure_empty_directory(directory)
        if ENV_PATH.exists():
            print("""
#######################################################################################
# WARNING! .env already existed and as been moved to .env.old                         #
# WARNING! Recreating a new .env file from .env.example                               #
# Please check .env and copy the variables from .env.old to .env when it makes sense. #
#######################################################################################
            """)
            try:
                ENV_PATH.replace(ENV_PATH.with_name(".env.old"))
            except Exception as ex:
                error(1, f"Failed to move {ENV_PATH} to {ENV_PATH.with_name('.env.old')}: {ex}")

    return directory


def download_needed_files(directory: Path, branch: str | None):
    files_to_download = [
            ("docker-compose.yml", directory / "docker-compose.yml"),
            (".env.example", directory / ".env.example"),
            ("nginx.conf", directory / "nginx.conf"),
        ]
    download_github_files(files_to_download, directory, branch)


def create_pg_password():
    # Ensure POSTGRES_PASSWORD exists in env file; otherwise create
    pg_pwd_regex = get_regex("POSTGRES_PASSWORD")
    env = read_env()
    pg_password = pg_pwd_regex.search(env)
    if not pg_password or strip_quotes(pg_password.group(1)) == "":
        verbose("Generating postgres password...")
        new_pass = generate_key(ALLOWED_PG_PASS_CHARS, 16)
        if not pg_password:
            env += f"POSTGRES_PASSWORD='{new_pass}'"
        else:
            env.replace(pg_password.group(0), f"POSTGRES_PASSWORD='{new_pass}'")
        write_env(env)
    else:
        verbose("Postgres password already exists, skipping...")


def install_cousins_matter(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Install Cousins Matter docker environment")
    parser.add_argument("-q", action="store_true", help="quiet mode, default is verbose")
    parser.add_argument("-e", action="store_true",
                        help="""create environment only (no download, assumes the files needed
                        to be downloaded are already there, ie in a CI/CD workflow)""")
    parser.add_argument("-d", dest="directory", default=None,
                        help="""the target directory where cousins-matter will be installed,
defaults to "." if -e is specified, otherwise ./cousins-matter.
In this case, directory must not exist or be empty.""")
    parser.add_argument("-b", dest="branch", default=None, help="branch to use (default: latest release)")
    parser.add_argument("-n", dest="no_editor", action="store_true", help="do not start an editor to edit .env")

    args = parser.parse_args(argv)
    set_verbose(not args.q)
    create_environment_only = args.e

    require_docker()

    directory = get_directory(create_environment_only, args.directory)

    if not create_environment_only:
        # Normal install: download files
        download_needed_files(directory, args.branch)

        # Create .env from .env.example if .env is missing
        verbose("Creating .env from .env.example...")
        try:
            (directory / ".env.example").replace(directory / ".env")
        except Exception as ex:
            error(1, f"Failed to create .env from .env.example: {ex}")

    verbose("Generating secret key...")
    rotate_secrets()

    create_pg_password()

    if create_environment_only:
        print("""
#####################################
# Review of cousins-matter env done #
#####################################
""")
    else:
        print("""
Installation of Cousins Matter done.
An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site.
TAKE INTO ACCOUNT THE POSSIBLE WARNINGS ON .env above
(don't change the SECRET_KEY and the POSTGRES_PASSWORD, they were generated automatically).
You can hit Ctrl-C to skip the editor if you want to see more details about the warnings above and edit manually .env
""")
        if not args.no_editor:
            for i in range(10, 0, -1):
                print(f"The editor will open in {i} seconds...\r", end="", flush=True)
                time.sleep(1)
            print()  # newline after countdown
            editor = os.environ.get("EDITOR", "editor")
            try:
                run([editor, ".env"], check=False)
            except Exception:
                pass
            print(f"""
    #############################################################################################
    # If you did set your environment variables correctly, you can now cd to your directory     #
    # {directory} and start the container with 'docker compose up -d'                           #
    # You can check the logs with 'docker compose logs -f'                                      #
    #############################################################################################
    """)
        else:
            print("""
    ######################################################################################
    # You can now edit .env to set your environment variables, then cd to your directory #
    # {directory} and start the container with 'docker compose up -d'                    #
    # You can check the logs with 'docker compose logs -f'                               #
    ######################################################################################
    """)


if __name__ == "__main__":
    install_cousins_matter()
