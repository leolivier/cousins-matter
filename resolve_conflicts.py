import os
import re
import subprocess


def resolve_conflict(content):
  # Pattern to find merge conflicts
  pattern = re.compile(r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [0-9a-f]+.*?\n", re.DOTALL)

  def replacement(match):
    ours = match.group(1)
    theirs = match.group(2)

    # Strategy: take theirs (logic) but we will ruff-format later
    # Actually, if we want to be safe, let's see if we can just take theirs
    # and hope ruff fixes the 4-space indent.
    return theirs + "\n"

  return pattern.sub(replacement, content)


def main():
  # Get unmerged files
  unmerged_files = subprocess.check_output(["git", "status", "--short"]).decode("utf-8")
  files = [line[3:] for line in unmerged_files.splitlines() if line.startswith("UU ")]

  for file in files:
    if not os.path.exists(file):
      continue
    print(f"Resolving {file}...")
    with open(file, "r") as f:
      content = f.read()

    # Check if it has markers
    if "<<<<<<< HEAD" in content:
      new_content = resolve_conflict(content)
      with open(file, "w") as f:
        f.write(new_content)

    # Add and format
    subprocess.run(["git", "add", file])
    subprocess.run(["ruff", "format", file])
    subprocess.run(["git", "add", file])


if __name__ == "__main__":
  main()
