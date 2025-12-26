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

# set the superuser variables in .env
sed -i 's/ADMIN=.*/ADMIN=admin/;s/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=123456/;s/ADMIN_EMAIL=.*/ADMIN_EMAIL=admin@example.com/;s/ADMIN_FIRSTNAME=.*/ADMIN_FIRSTNAME=Cousins/;s/ADMIN_LASTNAME=.*/ADMIN_LASTNAME=Matter;/' .env
export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-$tag}
echo "tested image: $COUSINS_MATTER_IMAGE"
echo "env: $(grep ADMIN .env)"

docker_run_cousins_matter

docker compose down -v
rm -rf "$tmpdir"
echo "test install passed"

