#!/usr/bin/env bash
#set -xe
repo=${1:-cousins-matter}
gh api repos/leolivier/$repo/actions/artifacts \
  --paginate \
  --jq '.artifacts[] | select(.name == "test-docker-image" and .expired == true) | .id' |
while read id; do
  echo "Deleting $id"
  gh api --method DELETE repos/leolivier/$repo/actions/artifacts/$id
done
