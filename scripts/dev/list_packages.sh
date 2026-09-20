
#!/usr/bin/env bash

repo=${1:-cousins-matter}

gh api repos/leolivier/$repo/actions/artifacts \
  --paginate \
  --jq '.artifacts[] | [.id, .name, (.size_in_bytes / 1048576 | floor), .created_at, .expired] | @tsv'
