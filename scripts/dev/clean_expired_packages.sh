#!/usr/bin/env bash
# Deletes GitHub Actions artifacts older than $days (default 10), whatever their name or expired flag.
#set -xe
repo=${1:-cousins-matter}
days=${2:-10}
cutoff=$(date -u -d "$days days ago" +%Y-%m-%dT%H:%M:%SZ)

gh api repos/leolivier/$repo/actions/artifacts \
  --paginate \
  --jq ".artifacts[] | select(.created_at < \"$cutoff\") | [.id, .name, .created_at] | @tsv" |
while IFS=$'\t' read -r id name created; do
  echo "Deleting $id ($name, created $created)"
  gh api --method DELETE repos/leolivier/$repo/actions/artifacts/$id
done
