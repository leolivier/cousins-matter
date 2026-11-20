#!/usr/bin/env python3
import os
import sys
import requests

OWNER, PACKAGE = "leolivier", "cousins-matter"
API = f"https://api.github.com/users/{OWNER}/packages/container/{PACKAGE}/versions"
REGISTRY = f"https://ghcr.io/v2/{OWNER}/{PACKAGE}/manifests"
REMOVABLE_PREFIXES = ("dependabot-", "dev-", "worktree-", "feat-", "fix-", "leolivier-")
DRY_RUN = "--delete" not in sys.argv

TOKEN = os.environ["GITHUB_TOKEN"]  # scopes: read:packages + delete:packages
GH_HEADERS = {
  "Accept": "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  "Authorization": f"Bearer {TOKEN}",
}
ACCEPT = ", ".join([
  "application/vnd.oci.image.index.v1+json",
  "application/vnd.docker.distribution.manifest.list.v2+json",
  "application/vnd.oci.image.manifest.v1+json",
  "application/vnd.docker.distribution.manifest.v2+json",
])


def list_versions():
  versions, url = [], f"{API}?state=active&per_page=100"
  while url:
    r = requests.get(url, headers=GH_HEADERS, timeout=10)
    r.raise_for_status()
    versions += [v for v in r.json() if v["metadata"]["package_type"] == "container"]
    url = r.links.get("next", {}).get("url")
  return versions


def registry_headers():
  r = requests.get(
    "https://ghcr.io/token",
    params={"service": "ghcr.io", "scope": f"repository:{OWNER}/{PACKAGE}:pull"},
    auth=(OWNER, TOKEN),
    timeout=10,
  )
  r.raise_for_status()
  return {"Authorization": f"Bearer {r.json()['token']}", "Accept": ACCEPT}


def child_digests(digest, headers):
  """Digests referenced by an index (platforms + attestations)."""
  r = requests.get(f"{REGISTRY}/{digest}", headers=headers, timeout=10)
  if r.status_code == 404:
    return []
  r.raise_for_status()  # on any other error: abort rather than risk deleting
  return [m["digest"] for m in r.json().get("manifests", [])]


def is_removable_tags(tags):
  return all(t.startswith(REMOVABLE_PREFIXES) for t in tags)  # True if tags == []


versions = list_versions()
reg = registry_headers()

# 1. Everything reachable from a "real" tag is protected
keep = set()
for v in versions:
  tags = v["metadata"]["container"].get("tags", [])
  if tags and not is_removable_tags(tags):
    keep.add(v["name"])
    keep.update(child_digests(v["name"], reg))

# 2. Delete everything else
for v in versions:
  if v["name"] in keep:
    continue
  tags = v["metadata"]["container"].get("tags", [])
  print(f"{'[dry-run] ' if DRY_RUN else ''}removing {v['id']} {v['name'][:19]} {tags}")
  if not DRY_RUN:
    requests.delete(f"{API}/{v['id']}", headers=GH_HEADERS, timeout=10).raise_for_status()

print(f"Kept {len(keep)} versions. {'Re-run with --delete to apply.' if DRY_RUN else 'Done.'}")
