#!/bin/sh

# this script is expected to be run from the root of the dev environment project

# import utils functions and variables
. "$(cd "$(dirname "$0")" && pwd)"/test_utils.sh

get_args "Runs a V1 to V2 cousins matter migration test" "$@"
set_variables

tmpdir=$(mktemp -d)

script_dir=$(cd "$(dirname "$0")" && cd .. && pwd)

echo "creating a copy of a test V1 instance of cousins-matter in $tmpdir"
unzip -q "$script_dir/tests/resources/cm-v1-tests.zip" -d "$tmpdir"
cd "$tmpdir"
# .env was existing before migration
[ ! -f .env ] && error 1 "No .env file found in $tmpdir"
# no need to set the superuser variables as the superuser must already exist in tha database
# the postgres password is added by the migration tool
export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-$tag}
echo "tested image: $COUSINS_MATTER_IMAGE"

python "$script_dir/manage_cousins_matter.py" migrate-v1-v2 -d "$tmpdir" "$release_or_branch" "$ref" || error 1 "manage_cousins_matter failed to migrate from v1 to v2"

docker_run_cousins_matter

# copy the sqlite database to a directory mounted in the container (data does not exist anymore in the container)
cp data/db.sqlite3 media/public/db.sqlite3
docker exec "cousins-matter" python -m scripts.tests.check_after_migration
rm media/public/db.sqlite3
docker compose down -v
cd ..
sudo rm -rf "$tmpdir"
echo "test migrate v1 to v2 passed"

