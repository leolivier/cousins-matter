#!/usr/bin/env python3

import argparse
import json
import os
import re
import secrets
import shutil
import string
import subprocess
import stat
import sys
import time
from urllib.request import urlopen
from pathlib import Path


CONTAINER = "cousins-matter"
IMAGE = f"ghcr.io/leolivier/{CONTAINER}"
GITHUB_REPO = "leolivier/cousins-matter"

# ANSI colors
ON_RED = "\x1b[41m"
ON_GREEN = "\x1b[42m\x1b[1;37m"
ON_WHITE = "\x1b[47m\x1b[1;30m"
NC = "\x1b[0m"
ENV_PATH = Path(".env")  # set correctly with directory in functions

VERBOSE = True


########################
#  UTILITIES
########################
def verbose(*msg: str, **kwargs) -> None:
  """Will print the given message if verbose is enabled"""
  if VERBOSE:
    print(" ".join(hide_if_secret(m) for m in msg), flush=True, **kwargs)


def set_verbose(v: bool) -> None:
  """Will set the verbose flag"""
  global VERBOSE
  VERBOSE = v


def warning(*msg: str) -> None:
  """Will print the given message in RED to stderr but won't exist"""
  print(f"{ON_RED}{' '.join(hide_if_secret(m) for m in msg)}{NC}", file=sys.stderr)


def error(code: int, *msg: str) -> None:
  """Will print the given message to stderr and exit with the given code"""
  warning(*msg)
  sys.exit(code)


def framed(msg: str) -> str:
  """Will return the given message framed with '#'"""
  lines = msg.splitlines()
  max_len = max(len(line) for line in lines) + 4  # add 4 for padding (2 spaces + 2#)
  for i, line in enumerate(lines):
    lines[i] = f"# {line}" + " " * (max_len - len(line) - 3) + "#"
  return "\n".join(["#" * max_len] + lines + ["#" * max_len])


def get_regex(key: str) -> re.Pattern[str]:
  """Will return a regex pattern to match the given key in a .env file"""
  r = r"=('[^']+'|\"[^\"]+\"|[^\s]*)[\s]*(#.*)?$"
  return re.compile(f"^{key}{r}$", flags=re.MULTILINE)


def generate_key(allowed_chars: str, length: int = 64) -> str:
  """Will generate a random key of the given length using the allowed characters"""
  return "".join(secrets.choice(allowed_chars) for _ in range(length))


def strip_quotes(s: str) -> str:
  """Will strip quotes from the given string if it is enclosed in quotes"""
  if len(s) >= 2 and ((s[0] == s[-1]) and s[0] in ("'", '"')):
    return s[1:-1]
  return s


SECRET_MARK_PATTERN = re.compile(r"##!(.*?)!##", re.S)


def mark_as_secret(string: str) -> str:
  return f"##!{string}!##"


def hide_if_secret(string: str) -> str:
  return SECRET_MARK_PATTERN.sub("[***]", string)


def clean_secret_mark(string: str) -> str:
  return SECRET_MARK_PATTERN.sub(lambda m: m.group(1), string)


def run(
  cmd: list[str],
  check=True,
  capture_output=False,
  text=True,
  quiet=False,
  cwd: str | None = None,
):
  """Will run the given shell command and return the result"""
  verbose("$", " ".join(cmd))
  return subprocess.run(
    [clean_secret_mark(c) for c in cmd],
    check=check,
    capture_output=capture_output,
    text=text,
    cwd=cwd,
  )


def require_docker():
  """Will check if docker is installed and raise an error if not"""
  try:
    subprocess.run(["docker", "--version"], check=True, capture_output=True, text=True)
  except Exception:
    error(1, "docker is not installed, please install it and restart the command")


def read_env() -> str:
  """Will return the content of the .env file"""
  try:
    return ENV_PATH.read_text(encoding="utf-8")
  except FileNotFoundError:
    error(1, f"{ENV_PATH} file not found")
  except Exception as ex:
    error(1, f"Failed to read {ENV_PATH}: {ex}")


def write_env(content: str) -> None:
  """Will write the given content to the .env file"""
  try:
    ENV_PATH.write_text(content, encoding="utf-8")
  except Exception as ex:
    error(1, f"Failed to write {ENV_PATH}: {ex}")


def docker_logs(container: str) -> str:
  """Will return the logs of the given container"""
  try:
    res = subprocess.run(["docker", "logs", container], check=False, capture_output=True, text=True)
    return res.stdout + (res.stderr or "")
  except Exception as ex:
    return str(ex)


def github_latest_release(repo: str) -> str:
  """Will return the latest release tag of the given repo from GitHub API"""
  url = f"https://api.github.com/repos/{repo}/releases/latest"
  with urlopen(url) as resp:
    data = json.load(resp)
  tag = data.get("tag_name")
  if not tag:
    raise RuntimeError("Could not determine latest release tag from GitHub API")
  return tag


def get_github_base_url(branch: str | None, release: str | None) -> str:
  """Will return the base URL for the given branch or release if branch is None.
  Default release is latest if branch is None"""
  if branch and not release:
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/{branch}"
  else:
    release = release or "latest"
    if release == "latest":
      try:
        release = github_latest_release(GITHUB_REPO)
      except Exception as ex:
        error(1, f"Failed to obtain latest release from GitHub: {ex}")
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/tags/{release}"


def download_github_file(file: str, dest: Path, base_url: str):
  """Will download file from GitHub and save it in the given destination
  Args:
      file: relative path of the file to download
      dest: destination path
      base_url: base URL to download from
  """
  url = f"{base_url}/{file}"
  verbose(f"Downloading {file} from {url}")
  try:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # download url to dest file
    with urlopen(url) as resp, open(dest, "wb") as f:
      shutil.copyfileobj(resp, f)
  except Exception as ex:
    error(1, f"Downloading {file} failed: {ex}")


def download_V2_needed_files(directory: Path, branch: str | None, release: str | None):
  files_to_download = [
    ("docker-compose.yml", directory / "docker-compose.yml"),
    (".env.example", directory / ".env.example"),
    ("config/nginx.conf", directory / "config" / "nginx.conf"),
    (
      "config/nginx.d/errors/413.html",
      directory / "config" / "nginx.d" / "errors" / "413.html",
    ),
  ]
  base_url = get_github_base_url(branch, release)
  for rel, dest in files_to_download:
    download_github_file(rel, dest, base_url)
  # copy myself to scripts/ (already downloaded)
  script_dir = directory / "scripts"
  script_dir.mkdir(parents=True, exist_ok=True)
  try:
    shutil.copy(__file__, script_dir)
  except shutil.SameFileError:
    pass


def check_cousins_matter_is_down():
  """Check if Cousins Matter is down
  will check containers and networks with name starting with cousins-matter
  """
  try:
    result = run(
      [
        "docker",
        "ps",
        "-a",
        "--filter",
        "name=cousins-matter",
        "--format",
        "json",
      ],
      check=True,
      capture_output=True,
      text=True,
    )
    if result.returncode != 0:
      error(1, "Unable to check if cousins-matter is down")
    containers = json.loads(f"[{','.join(result.stdout.splitlines())}]")
    errors = []
    for container in containers:
      name = container.get("Names", "")
      state = container.get("State", "")
      status = container.get("Status", "")
      match state:
        case "running":
          errors.append(f"""{name} is already running ({status}),
please stop it and remove the container before running this script""")
        case "exited":
          errors.append(f"""{name} is already stopped ({status})
but the container is still there, please remove it before running this script""")
        case _:
          errors.append(f"""{name} is in an unknown state ({state}),
please remove the container before running this script""")
  except subprocess.CalledProcessError as e:
    error(1, f"Unable to check if cousins-matter containers are down: {e}")

  result = run(
    ["docker", "network", "ls", "--filter", "name=cousins_matter", "-q"],
    check=True,
    capture_output=True,
    text=True,
  )

  if result.returncode != 0:
    error(1, "Unable to check if cousins-matter networks are down")
  if result.stdout != "":
    errors.append(f"""This cousins-matter network is still up: {result.stdout},
please remove it before running this script""")
  if errors:
    error(1, "\n".join(errors))


def create_pg_password():
  """Ensure POSTGRES_PASSWORD exists in env file; otherwise create"""
  pg_pwd_regex = get_regex("POSTGRES_PASSWORD")
  env = read_env()
  pg_password = pg_pwd_regex.search(env)
  if not pg_password or strip_quotes(pg_password.group(1)) == "":
    verbose("Generating postgres password...")
    ALLOWED_PG_PASS_CHARS = string.ascii_letters + string.digits + "./_*"
    new_pass = generate_key(ALLOWED_PG_PASS_CHARS, 16)
    if not pg_password:
      env += f"\nPOSTGRES_PASSWORD='{new_pass}'\n"
    else:
      env = env.replace(pg_password.group(0), f"POSTGRES_PASSWORD='{new_pass}'")
    write_env(env)
    return new_pass
  else:
    verbose("Postgres password already exists, skipping...")
    return strip_quotes(pg_password.group(1))


#######################################
#  ROTATE SECRETS
#######################################


def rotate_secrets(args: argparse.Namespace | None = None) -> int:
  "Rotate SECRET_KEY in .env and maintain PREVIOUS_SECRET_KEYS"
  # regex and allowed chars
  SEC_REGEX = get_regex("SECRET_KEY")
  PREV_REGEX = get_regex("PREVIOUS_SECRET_KEYS")
  # Allowed characters for SECRET_KEY
  SECRET_KEY_ALLOWED_CHARS = string.ascii_letters + string.digits + "!@#$%^*()_-+{}[]:;<>?."

  # Load .env
  env = read_env()

  # If SECRET_KEY missing: create and append comment + keys, then exit 1
  secret_match = SEC_REGEX.search(env)
  if secret_match is None:
    verbose("no SECRET_KEY variable found in .env, generating one")
    new_key = generate_key(SECRET_KEY_ALLOWED_CHARS)
    env += f"""
# Don't change these 2 lines, they are automatically generated by rotate-secrets.sh
SECRET_KEY='{new_key}'
PREVIOUS_SECRET_KEYS=''
"""
    write_env(env)
    return 1

  old_secret = strip_quotes(secret_match.group(1))
  # Rotate SECRET_KEY
  new_key = generate_key(SECRET_KEY_ALLOWED_CHARS)
  env = env.replace(secret_match.group(0), f"SECRET_KEY='{new_key}'")

  # Update PREVIOUS_SECRET_KEYS
  prev_secret_match = PREV_REGEX.search(env)
  if prev_secret_match is None:  # no prev secrets, generate one
    env += f"PREVIOUS_SECRET_KEYS='{old_secret}'"
  else:
    prev_val = strip_quotes(prev_secret_match.group(1))
    combined = f"{prev_val},{old_secret}" if old_secret else prev_val
    env = env.replace(prev_secret_match.group(0), f"PREVIOUS_SECRET_KEYS='{combined}'")

  write_env(env)

  verbose("""Old SECRET_KEY added to PREVIOUS_SECRET_KEYS in .env
SECRET_KEY rotated successfully""")
  return 0


#######################################
#  V1.X TO V2 MIGRATION FUNCTIONS
#######################################


def check_if_cousins_matter_V1_directory(directory: Path):
  """Will check if the given directory is a Cousins Matter V1.x project directory"""
  make_sure = f"{ON_RED}Please make sure first you are in a cousins-matter V1.x directory before running this script{NC}"
  global ENV_PATH
  ENV_PATH = directory / ".env"
  if not ENV_PATH.is_file():
    error(10, "No .env file found in the directory.", make_sure)
  if not (directory / "docker-compose.yml").is_file():
    error(11, "No docker-compose.yml file found in the directory.", make_sure)
  data_dir = directory / "data"
  if not data_dir.is_dir():
    error(12, "No data directory found in the directory.", make_sure)
  if not (data_dir / "db.sqlite3").is_file():
    error(13, "No db.sqlite3 file found in the data directory.", make_sure)
  media_dir = directory / "media"
  if not media_dir.is_dir():
    error(14, "No media directory found in the directory.", make_sure)


def check_permissions(directory: Path):
  media_dir = directory / "media"
  all_dirs = [media_dir] + [d for d in media_dir.rglob("*/")]
  cur_uid = os.getuid()
  warn = False
  try:
    for dir in all_dirs:
      st = dir.stat()
      if st.st_uid == 1000:
        if (st.st_mode & stat.S_IWUSR) != stat.S_IWUSR:  # dir is not writable by user 1000
          if cur_uid == st.st_uid or cur_uid == 0:  # current user is also 1000 or root, let's chmod
            dir.chmod(st.st_mode | stat.S_IWUSR)
          else:
            warn = True
            break
      else:
        warn = True
        break
  except Exception as ex:
    error(14, f"Error while checking permissions: {ex}")
  finally:
    if warn:
      warning(f"media directory {media_dir} and ALL its subdirectories must be owned and writable by user 1000")
      warning("Please, run the 2 following commands before tryning to start Cousins Matter:")
      print(f"{ON_WHITE}sudo chown -R 1000:1000 {media_dir}{NC}")
      print(f"{ON_WHITE}sudo chmod -R u+w {media_dir}{NC}")


def migrate_sqlite3_to_postgres(pg_pwd: str):
  """Will run the database migration from sqlite3 to postgres"""
  # Start postgres and wait for readiness
  verbose("Starting postgres server...")
  r = run(
    ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "30", "postgres"],
    check=False,
  )
  if r.returncode != 0:
    run(["docker", "compose", "logs", "postgres"], check=False)
    run(["docker", "compose", "down", "-v", "postgres"], check=False)
    error(
      17,
      """Postgres failed to start, see error message above, try to fix it, then rerun this script""",
    )
  verbose("Postgres is ready, starting migration...")

  # Run pgloader
  arch = os.uname().machine
  match arch:
    case "aarch64":
      pgloader_image = "ghcr.io/notagshen/pgloader-arm64:latest"
    case "x86_64":
      pgloader_image = "dimitri/pgloader:latest"
    case _:
      raise RuntimeError(f"Unsupported OS architecture: {arch}")

  postgres_user = os.getenv("POSTGRES_USER") or "cousinsmatter"
  postgres_db = os.getenv("POSTGRES_DB") or "cousinsmatter"
  postgres_port = os.getenv("POSTGRES_PORT") or "5432"
  r = run(
    [
      "docker",
      "run",
      "--entrypoint",
      "pgloader",
      "-v",
      "./data:/data",
      "--network",
      "cousins_matter_network",
      "--name",
      "cousins-matter-pgloader",
      pgloader_image,
      "sqlite:///data/db.sqlite3",
      f"postgresql://{postgres_user}:{mark_as_secret(pg_pwd)}@postgres:{postgres_port}/{postgres_db}",
    ],
    check=False,
  )
  if r.returncode != 0:
    run(["docker", "down", "-v", "postgres"], check=False)
    run(["docker", "rm", "-v", "cousins-matter-pgloader"], check=False)
    error(
      16,
      """Database migration failed, see error message, try to fix it, then rerun this script""",
    )

  verbose("Database migration done, removing pgloader container...")
  subprocess.run(["docker", "container", "rm", "cousins-matter-pgloader"], check=False)

  print(f"""
{ON_GREEN}Your database has now been migrated to postgres, you can start Cousins Matter with 'docker compose up -d'{NC}
{ON_RED}IMPORTANT:{NC}
{ON_WHITE}Don't remove the db.sqlite3 file until you have checked that the postgres database has been correctly
initialized.{NC}
Navigate in your site and check that all data is there.
{ON_RED}TIP:{NC} You can also have a look at the migration log in the table above and check that the number of migrated
rows is correct.
Look specifically at 'members_member' (the number of members), 'galleries_gallery' (the number of galleries),
'galleries_photo' (the number of photos), 'forum_post' (the number of forum posts), 'chat_chatroom' and 'chat_privatechatroom'
(the number of public and private chat rooms), 'polls_poll' (the number of polls), 'classified_ads_classifiedad' (the number
of classified ads), and 'troves_trove' (the number of \"treasures\") to make sure they are correct.
If everything is correct, you can remove the db.sqlite3 file.
As redis is now using a named volume, you can remove the redis data directory if you want to, and thus the whole data
directory which is not needed anymore.
""")


def migrate_v1_v2(args):
  """Migrates Cousins Matter from v1 to v2."""

  directory = Path(args.directory).resolve()

  # check docker is installed
  require_docker()

  verbose(f"{ON_WHITE}Migrating Cousins Matter from v1.x to v2...{NC}")
  verbose(f"Checking if directory {directory} looks like a cousins-matter project...")

  if not directory.exists() or not directory.is_dir():
    error(1, f"Error: directory {directory} does not exist")

  os.chdir(directory)

  check_if_cousins_matter_V1_directory(directory)

  check_cousins_matter_is_down()

  check_permissions(directory)

  # add the new needed postgres password to .env
  pg_pwd = create_pg_password()

  verbose("Creating config and static directories...")
  Path("config").mkdir(parents=True, exist_ok=True, mode=0o777)
  Path("static").mkdir(parents=True, exist_ok=True, mode=0o777)

  # verbose(f"Fixing permissions...")
  # fix_permissions()

  verbose("Downloading v2 scripts...")
  download_V2_needed_files(directory, branch=args.branch, release=args.release)

  verbose("Rotating secrets...")
  rotate_secrets()

  verbose("Migrating database...")
  migrate_sqlite3_to_postgres(pg_pwd)

  verbose("Pulling new docker images...")
  run(["docker", "compose", "pull"])


####################################
# INSTALLATION FUNCTIONS
####################################
def ensure_empty_directory(directory: Path):
  """Ensure the directory is empty, create it if it doesn't exist
  Check if it contains any entry which is not scripts, media or static directory
  """
  if not directory.exists():
    directory.mkdir(parents=True, exist_ok=True)
    return
  if any(
    filter(
      lambda x: not x.is_dir() or x.name not in ["scripts", "media", "static"],
      directory.iterdir(),
    )
  ):
    error(
      1,
      f"{directory} is not empty, cousins-matter must be installed in an empty directory.",
    )


def check_envfile(directory: Path, review_environment: bool):
  """Check for .env file existence
  If review_environment is True, ensure .env exists; if not, print warning
  Otherwise, ensure directory is empty and move .env to .env.old if it exists after printing warning
  """
  global ENV_PATH
  ENV_PATH = directory / ".env"
  if review_environment:
    if not ENV_PATH.exists():
      print(
        framed("""WARNING! '-e' param was provided and skipped dowloading .env.example. However, .env
does not exist in this directory. Please check .env.example, .env.old if it exists, and
create a .env file to make sure all required variables are present.""")
      )
  else:
    # Normal install: ensure directory is empty and move .env to .env.old if it exists
    ensure_empty_directory(directory)
    if ENV_PATH.exists():
      print(
        framed("""WARNING! .env already existed and as been moved to .env.old
WARNING! Recreating a new .env file from .env.example
WARNING! Please check .env and copy the variables from .env.old to .env when it makes sense.""")
      )
      try:
        ENV_PATH.replace(ENV_PATH.with_name(".env.old"))
      except Exception as ex:
        error(
          1,
          f"Failed to move {ENV_PATH} to {ENV_PATH.with_name('.env.old')}: {ex}",
        )


def get_directory(review_environment: bool, directory: str | None):
  """Resolve directory based on review_environment param. directory param is optional and comes from argv.
  Creates media and config directories if they do not exist.
  """
  cwd = Path.cwd()
  if review_environment:  # review environment only
    directory = Path(directory or cwd).resolve()
    # Ensure we're running from scripts dir
    script_dir_name = Path(__file__).resolve().parent.name
    if script_dir_name != "scripts":
      error(
        1,
        "this script should be run from the scripts directory if -e selected. Are you in a devt environment?",
      )
  else:
    directory = Path(directory or (cwd / "cousins-matter")).resolve()

  try:
    directory.mkdir(parents=True, exist_ok=False)
    verbose(f"directory {directory} does not exist, creating it...")
  except FileExistsError:
    verbose(f"directory {directory} already exists.")

  check_envfile(directory, review_environment)

  os.chdir(directory)
  try:
    directory.chmod(0o777)
  except Exception as ex:
    error(1, f"Failed to set permissions for {directory}: {ex}")

  Path("media").mkdir(parents=True, exist_ok=True, mode=0o777)
  Path("config").mkdir(parents=True, exist_ok=True, mode=0o777)
  Path("static").mkdir(parents=True, exist_ok=True, mode=0o777)

  return directory


def install_cousins_matter(args):
  """
  install files and directories for Cousins Matter.
  see --help for more details
  """

  require_docker()
  check_cousins_matter_is_down()  # just in case we have sevaral tests running at the same moment
  directory = get_directory(args.review_environment, args.directory)

  if not args.review_environment:
    # Normal install: download files
    download_V2_needed_files(directory, args.branch, args.release)

    # Create .env from .env.example if .env is missing
    verbose("Creating .env from .env.example...")
    try:
      ENV_PATH.with_name(".env.example").replace(ENV_PATH)
    except Exception as ex:
      error(1, f"Failed to create .env from .env.example: {ex}")

  verbose("Generating secret key...")
  rotate_secrets()

  create_pg_password()

  if args.review_environment:
    print(framed("Review of cousins-matter env done"))
  else:
    print(framed("         Installation of Cousins Matter done!         "))
    if not args.no_editor:
      print("""
An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site.
TAKE INTO ACCOUNT THE POSSIBLE WARNINGS ON .env above
(don't change the SECRET_KEY and the POSTGRES_PASSWORD, they were generated automatically).
You can hit Ctrl-C to skip the editor if you want to see more details about the warnings above and edit manually .env
""")
      for i in range(10, 0, -1):
        print(f"The editor will open in {i} seconds...\r", end="", flush=True)
        time.sleep(1)
      print()  # newline after countdown
      editor = os.environ.get("EDITOR", "editor")
      try:
        run([editor, str(ENV_PATH)], check=True)
      except Exception as e:
        print(
          f"{ON_RED}Couldn't start the editor automatically ({e}), please start it manually and edit the {ENV_PATH} file.{NC}"
        )

      print(
        framed(f"""
Once your environment variables are set properly in {str(ENV_PATH)}, you can cd to your directory
{directory} and start the container with 'docker compose up -d'
You can check the logs with 'docker compose logs -f'""")
      )
    else:
      print(
        framed(f"""
You can now edit .env to set your environment variables, then cd to your directory
{directory} and start the container with 'docker compose up -d'
You can check the logs with 'docker compose logs -f'""")
      )


######################
# MAIN
######################
def main(argv=None):
  if argv is None:
    argv = sys.argv[1:]

  # Main parser (global options)
  parser = argparse.ArgumentParser(
    prog="manage_cousins_matter",
    description="""
Manage Cousins Matter utilities. Provides several commands (see below). To get help on a specific command, use:
manage_cousins_matter <command> -h""",
  )
  # Global options (can be placed before the subcommand)
  parser.add_argument(
    "-q",
    "--quiet",
    action="store_true",
    dest="quiet",
    help="quiet mode (default mode is verbose)",
  )

  # Subcommands
  subparsers = parser.add_subparsers(dest="command", required=True, help="command")

  # Migrate subcommand
  p_migrate = subparsers.add_parser(
    "migrate-v1-v2",
    help="""
Migrates Cousins Matter from v1.x to v2: after some checks, migrates the sqlite3 database to postgres, downloads v2 files
from GitHub, and rotates the secret key.
    """,
  )
  p_migrate.add_argument(
    "-d",
    "--directory",
    dest="directory",
    default=os.getcwd(),
    help="cousins-matter directory (default: current directory)",
  )
  p_migrate.add_argument(
    "-b",
    "--branch",
    dest="branch",
    default=None,
    help="""
branch to use (default: none, -r always takes precedence)""",
  )
  p_migrate.add_argument(
    "-r",
    "--release",
    dest="release",
    default=None,
    help="""
release to use (default: latest release, takes precedence over -b)""",
  )
  p_migrate.set_defaults(func=migrate_v1_v2)

  # Install subcommand
  p_install = subparsers.add_parser(
    "install",
    help="""
Install Cousins Matter local files and directories. After some checks, it will download a few files
from GitHub. Then, it will rotate/generate the secret key and the postgres password if missing, create
needed directories with appropriate permissions, and finally open an editor on .env after a countdown.
    """,
  )
  p_install.add_argument(
    "-e",
    "--review-environment",
    action="store_true",
    dest="review_environment",
    help="""
review environment only. No download, assumes .env and the files needed to be downloaded are already there,
ie in a CI/CD workflow""",
  )
  p_install.add_argument(
    "-d",
    "--directory",
    dest="directory",
    default=None,
    help="""
the target directory where cousins-matter will be installed. Defaults is "." if -e is specified, otherwise
./cousins-matter. In this case, directory must either not exist or be empty.""",
  )
  p_install.add_argument(
    "-b",
    "--branch",
    dest="branch",
    default=None,
    help="""
branch to use for downloading files from GitHub (default: none, -r always takes precedence)""",
  )
  p_install.add_argument(
    "-r",
    "--release",
    dest="release",
    default=None,
    help="""
Release to use for downloading files from GitHub (default: latest release, always takes precedence over -b)""",
  )
  p_install.add_argument(
    "-n",
    "--no-editor",
    dest="no_editor",
    action="store_true",
    help="""
do not start an editor to edit .env at the end of the process""",
  )
  p_install.set_defaults(func=install_cousins_matter)

  # Rotate secrets subcommand
  p_rotate_secrets = subparsers.add_parser(
    "rotate-secrets",
    help="""
Rotate SECRET_KEY and update PREVIOUS_SECRET_KEYS in .env""",
  )
  p_rotate_secrets.set_defaults(func=rotate_secrets)

  # Parse and execution
  args = parser.parse_args(argv)
  set_verbose(not args.quiet)

  # Call the function linked to the subcommand
  args.func(args)


if __name__ == "__main__":
  main()
