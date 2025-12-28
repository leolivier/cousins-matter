#!/bin/sh

# this script is expected to be run from the root of the dev environment project

# import utils functions and variables
. "$(cd "$(dirname "$0")" && pwd)"/test_utils.sh

get_args "Runs a Cousins Matter install test" "$@"
set_variables

tmpdir=$(mktemp -d)
echo "tmpdir: $tmpdir"

python ./scripts/manage_cousins_matter.py install -d "$tmpdir" "$release_or_branch" "$ref" -n || error 1 "manage_cousins_matter failed to install Cousins Matter"

cd "$tmpdir"
# .env must have been created by manage_cousins_matter install above
[ ! -f .env ] && error 1 "No .env file found in $tmpdir"

cat .env | grep -v "^#" | grep -v -e "^\s*$"

set_admin_env_vars
export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-$tag}
echo "tested image: $COUSINS_MATTER_IMAGE"

grep 'POSTGRES_PASSWORD' .env || error 1 "No POSTGRES_PASSWORD found in .env"

docker_run_cousins_matter

docker compose down -v
rm -rf "$tmpdir"
echo "test install passed"

