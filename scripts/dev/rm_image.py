#!/usr/bin/env python3
import os
import sys
import requests

print("This script removes all untagged versions of the package cousins-matter on ghcr.io")
print("Images without tags can be the one of each platform (amd64, arm64, etc.) and removing them will end up in")
print('an error "Manifest not found"! So USE WITH CAUTION!!!')
if input("Type 'GO' to continue: ") != "GO":
  sys.exit(0)

api = "https://api.github.com/users/leolivier/packages/container/cousins-matter/versions"
headers = {
  "Accept": "application/vnd.github+json",
  "X-GitHub-Api-Version": "2022-11-28",
  "Authorization": "Bearer " + os.getenv("GITHUB_TOKEN"),
}
get_url = f"{api}?state=active&per_page=100"
while True:
  response = requests.get(get_url, headers=headers)
  if response.status_code != 200:
    print(response.json())
    sys.exit(1)
  images = response.json()
  for image in images:
    # print(image)
    metadata = image["metadata"]
    if metadata["package_type"] != "container":
      continue
    if "tags" in metadata["container"]:
      # remove dependabot and dev images
      tags = metadata["container"]["tags"]
      start_tags = ["dependabot-", "dev-"]
      removed = True
      for tag in tags:
        if not any(tag.startswith(start_tag) for start_tag in start_tags):
          removed = False
          break
      if not removed:
        continue
    print(f"removing {api}/{image['id']} {metadata['container']['tags']}")
    requests.delete(f"{api}/{image['id']}", headers=headers)
  links = response.links
  if "next" in links:
    get_url = links["next"]["url"]
    continue
  else:
    print("Done")
    break
