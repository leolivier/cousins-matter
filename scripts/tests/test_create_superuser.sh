#!/bin/bash

# this script is expected to be run from the root of the dev environment project

# import utils functions and variables
source $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test_utils.sh

get_args "Runs a Cousins Matter install test" $@
set_variables

tmpdir=$(mktemp -d)
echo "tmpdir: $tmpdir"

python ./scripts/manage_cousins_matter.py install -d "$tmpdir" -b "$curbranch" -n
[[ $? != 0 ]] && error 1 "manage_cousins_matter failed to install Cousins Matter"

pushd "$tmpdir"

# .env must have been created by manage_cousins_matter install above
[[ ! -f .env ]] && error 1 "No .env file found in $tmpdir"

export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-"cousins-matter:$curbranch"}
echo "COUSINS_MATTER_IMAGE: $COUSINS_MATTER_IMAGE"

 # as we didn't fill the ADMIN_xxx variables in .env, the container will fail to create the superuser
docker_run_cousins_matter

# Now, set the superuser variables in .env before calling create_superuser
ADMIN=admin
ADMIN_PASSWORD=123456
ADMIN_EMAIL=admin@example.com
ADMIN_FIRSTNAME=Cousins
ADMIN_LASTNAME=Matter

# use temp file to avoid that sed changes the inode of the file while docker-compose is reading it
sed -e "s/^ADMIN=.*/ADMIN=${ADMIN}/" .env > .env.tmp  
for var in ADMIN ADMIN_PASSWORD ADMIN_EMAIL ADMIN_FIRSTNAME ADMIN_LASTNAME
do  
    sed -i -e "s/^$var=.*/$var=${!var}/" .env.tmp
done
cat .env.tmp > .env
rm .env.tmp

docker exec cousins-matter python -m scripts.create_superuser  # create_superuser self-checks

docker compose down -v
popd
rm -rf "$tmpdir"
echo "test create superuser passed"

