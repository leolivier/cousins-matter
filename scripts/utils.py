import json
import re
import secrets
import shutil
import subprocess
import sys
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
ENV_PATH = Path(".env")

VERBOSE = True


def verbose(*msg: str, **kwargs) -> None:
  if VERBOSE:
    print(" ".join(str(m) for m in msg), flush=True, **kwargs)


def set_verbose(v: bool) -> None:
  global VERBOSE
  VERBOSE = v


def get_regex(key: str) -> re.Pattern[str]:
    r = r"=('[^']+'|\"[^\"]+\"|[^\s]*)[\s]*$"
    return re.compile(f"^{key}{r}$", flags=re.MULTILINE)


def generate_key(allowed_chars: str, length: int = 64) -> str:
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def strip_quotes(s: str) -> str:
    if len(s) >= 2 and ((s[0] == s[-1]) and s[0] in ("'", '"')):
        return s[1:-1]
    return s


def run(cmd: list[str], check=True, capture_output=False, text=True, quiet=False, cwd: str | None = None):
    verbose("$", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=text, cwd=cwd)


def require_docker():
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True, text=True)
    except Exception:
        error(1, "docker is not installed, please install it and restart the command")


def error(code: int, *msg: str) -> None:
    print(f"{ON_RED}{' '.join(str(m) for m in msg)}{NC}", file=sys.stderr)
    sys.exit(code)


def read_env() -> str:
    try:
        return ENV_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        error(1, f"{ENV_PATH} file not found")
    except Exception as ex:
        error(1, f"Failed to read {ENV_PATH}: {ex}")


def write_env(content: str) -> None:
    try:
        ENV_PATH.write_text(content, encoding="utf-8")
    except Exception as ex:
        error(1, f"Failed to write {ENV_PATH}: {ex}")


def docker_logs(container: str) -> str:
    try:
        res = subprocess.run(["docker", "logs", container], check=False, capture_output=True, text=True)
        return res.stdout + (res.stderr or "")
    except Exception as ex:
        return str(ex)


def github_latest_release(repo: str) -> str:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    with urlopen(url) as resp:
        data = json.load(resp)
    tag = data.get("tag_name")
    if not tag:
        raise RuntimeError("Could not determine latest release tag from GitHub API")
    return tag


def download_github_files(files_to_download: list[tuple[str, Path]], directory: Path, branch: str | None):
    verbose(f"downloading {[file for file, _ in files_to_download]} from GitHub...")

    # Determine base URL
    if branch:
        base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/{branch}"
    else:
        try:
            last_release = github_latest_release(GITHUB_REPO)
            base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/tags/{last_release}"
        except Exception as ex:
            error(1, f"Failed to obtain latest release from GitHub: {ex}")

    for rel, dest in files_to_download:
        url = f"{base}/{rel}"
        verbose(f"Downloading {rel} from {url}")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            # download url to dest file
            with urlopen(url) as resp, open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
        except Exception as ex:
            error(1, f"Downloading {rel} failed: {ex}")
