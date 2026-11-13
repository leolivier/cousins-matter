#!/bin/sh

# Upgrades a v2 instance to v3 on the same PostgreSQL volume and checks the
# result. Expected to be run from the root of the dev environment project,
# after .env exists and has SECRET_KEY and POSTGRES_PASSWORD set (CI runs
# `manage_cousins_matter.py install -e -n -d "$GITHUB_WORKSPACE"` first).
#
# The v2 image is not pullable from GHCR anymore, build it from the tag first:
#   mkdir -p /tmp/cm-v2 && curl -fsSL \
#     https://github.com/leolivier/cousins-matter/archive/refs/tags/v2.6.1.tar.gz \
#     | tar -xz -C /tmp/cm-v2 --strip-components=1
#   docker build -t cm-v2:2.6.1 /tmp/cm-v2

# import utils functions and variables
# shellcheck source=SCRIPTDIR/test_utils.sh
. "$(cd "$(dirname "$0")" && pwd)"/test_utils.sh

get_args "Runs a V2 to V3 cousins matter upgrade test" "$@"
set_variables

script_dir=$(cd "$(dirname "$0")" && cd .. && pwd)
new_image="${COUSINS_MATTER_IMAGE:-$tag}"
v2_image="${V2_IMAGE:-cm-v2:2.6.1}"

[ -f .env ] || error 1 "No .env file found in $(pwd)"
[ -f docker-compose.yml ] || error 1 "No docker-compose.yml found in $(pwd)"
[ -z "$(docker compose ps --quiet)" ] || error 1 "Cousins Matter containers are already running, stop them first"

echo "v2 image: $v2_image"
echo "v3 image: $new_image"

echo "starting the v2 instance on a fresh database..."
COUSINS_MATTER_IMAGE="$v2_image" docker compose up -d --wait --wait-timeout 120 || error 1 "the v2 instance failed to start"

echo "seeding legacy v2 data..."
docker cp "$script_dir/tests/seed_v2_data.py" cousins-matter:/tmp/seed_v2_data.py || error 1 "failed to copy the v2 seed script"
docker exec cousins-matter python manage.py shell -c "exec(open('/tmp/seed_v2_data.py').read())" || error 1 "failed to seed v2 data"

echo "stopping v2 and starting v3 on the same database..."
docker compose down || error 1 "failed to stop the v2 instance"
COUSINS_MATTER_IMAGE="$new_image" docker compose up -d --wait --wait-timeout 180 --force-recreate || error 1 "the v3 instance failed to start after the upgrade"

docker exec cousins-matter python manage.py migrate --check || error 1 "pending migrations after the upgrade"
docker cp "$script_dir/tests/check_after_upgrade_v2_v3.py" cousins-matter:/tmp/check_after_upgrade_v2_v3.py || error 1 "failed to copy the post-upgrade check script"
docker exec cousins-matter python manage.py shell -c "exec(open('/tmp/check_after_upgrade_v2_v3.py').read())" || error 1 "post-upgrade checks failed"

docker compose down -v
echo "test v2 to v3 upgrade passed"
