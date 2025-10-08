#!/bin/bash

# this script is expected to be run from the root of the dev environment project
set -e
error() {
	code=$1
	shift
  echo "Error: $@" >&2
  docker compose down -v
  exit $code
}

curbranch=$(git branch --show-current)
[[ -z "$curbranch" ]] && error 1 "git branch --show-current returned an empty string. Please run this script from the root of the dev environment project."

tmpdir=$(mktemp -d)
echo "tmpdir: $tmpdir"

python ./scripts/manage_cousins_matter.py install -d "$tmpdir" -b "$curbranch" -n
[[ $? != 0 ]] && error 1 "manage_cousins_matter failed to install Cousins Matter"

pushd "$tmpdir"

# .env must have been created by manage_cousins_matter install above
[[ ! -f .env ]] && error 1 "No .env file found in $tmpdir"

export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-"cousins-matter:$curbranch"}
echo "COUSINS_MATTER_IMAGE: $COUSINS_MATTER_IMAGE"
(docker images --format "{{.Repository}}:{{.Tag}}" | grep $COUSINS_MATTER_IMAGE) || error 1 "Image $COUSINS_MATTER_IMAGE not found"

 # as we didn't fill the ADMIN_xxx variables in .env, the container will fail to create the superuser
docker compose up -d  --wait --wait-timeout 30
sleep 5 # let the system stabilize

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

