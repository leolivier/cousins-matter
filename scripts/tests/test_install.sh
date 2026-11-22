#!/bin/sh
set -x
# this script is expected to be run from the root of the dev environment project

# import utils functions and variables
# shellcheck source=SCRIPTDIR/test_utils.sh
. "$(cd "$(dirname "$0")" && pwd)"/test_utils.sh

get_args "Runs a Cousins Matter install test" "$@"
set_variables

tmpdir=$(mktemp -d)
echo "tmpdir: $tmpdir"

# CI runs from a checkout of the tested ref: install its files instead of
# downloading them (the tested repo may be private, which raw GitHub cannot
# serve unauthenticated, and the download would test the wrong code)
local_files=
[ -n "$github_action" ] && local_files="-l"
# shellcheck disable=SC2086  # $local_files is an optional flag, not a value
python ./scripts/manage_cousins_matter.py -R "$github_repo" -n "$container" install -d "$tmpdir" "$release_or_branch" "$ref" $local_files -n || error 1 "manage_cousins_matter failed to install Cousins Matter"

cd "$tmpdir"
# .env must have been created by manage_cousins_matter install above
[ ! -f .env ] && error 1 "No .env file found in $tmpdir"

set_admin_env_vars
grep -v "^#" .env | grep -v -e "^\s*$"
export COUSINS_MATTER_IMAGE="${COUSINS_MATTER_IMAGE:-$tag}"
echo "tested image: $COUSINS_MATTER_IMAGE"

grep 'POSTGRES_PASSWORD' .env || error 1 "No POSTGRES_PASSWORD found in .env"

# The install above generated a new POSTGRES_PASSWORD in a fresh .env, but postgres
# only applies it when initializing an empty data directory: wipe the volumes left
# behind by a previous failed/interrupted run or authentication will fail.
docker compose down -v
docker_run_cousins_matter

docker compose down -v
rm -rf "$tmpdir"
echo "test install passed"
