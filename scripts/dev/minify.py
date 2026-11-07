import argparse
import os
from pathlib import Path
import rcssmin
import rjsmin

EXCLUDE_DIRS = {"node_modules", ".venv", "venv", ".git", "__pycache__", "staticfiles"}


def iter_assets(root: Path):
  for dirpath, dirnames, filenames in os.walk(root):
    # mutate dirnames in place to prevent os.walk from descending into excluded dirs
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
    for name in filenames:
      if name.endswith((".css", ".js")) and not name.endswith((".min.css", ".min.js")):
        yield Path(dirpath) / name


def minify_all(root: Path):
  for f in iter_assets(root):
    text = f.read_text(encoding="utf-8")
    if f.suffix == ".css":
      out = f.with_suffix(".min.css")
      out.write_text(rcssmin.cssmin(text), encoding="utf-8")
    else:
      out = f.with_suffix(".min.js")
      out.write_text(rjsmin.jsmin(text), encoding="utf-8")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Minify .css and .js files recursively.")
  parser.add_argument("root", nargs="?", default=".", help="directory to scan (default: .)")
  args = parser.parse_args()
  minify_all(Path(args.root))
