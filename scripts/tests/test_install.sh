#!/bin/bash

# this script is expected to be run from the root of the dev environment project
set -e
error() {
	code=$1
	shift
  echo "Error: $@" >&2
  exit $code
}

curbranch=$(git branch --show-current)
[[ -z "$curbranch" ]] && error 1 "git branch --show-current returned an empty string. Please run this script from the root of the dev environment project."
if [[ -n $(git status -s) || -n $(git log @{u}..) ]]; then
    echo "###########################################################################################"
    echo "# WARNING! Some files may have been modified and not pushed to github.                    #"
    echo "# As some files are downloaded from github by manage_cousins_matter, the test might not   #"
    echo "# use modified local files. Please commit your changes before running this script.        #"
    echo "###########################################################################################"
		git status -s
		git log @{u}..
fi
tmpdir=$(mktemp -d)
echo "tmpdir: $tmpdir"
python ./scripts/manage_cousins_matter.py install -d "$tmpdir" -b "$curbranch" -n
[[ $? != 0 ]] && error 1 "manage_cousins_matter failed to install Cousins Matter"
cd $tmpdir
# .env must have been created by manage_cousins_matter install above
[[ ! -f .env ]] && error 1 "No .env file found in $tmpdir"
# set the superuser variables in .env 
ADMIN=admin
ADMIN_PASSWORD=123456
ADMIN_EMAIL=admin@example.com
ADMIN_FIRSTNAME=Cousins
ADMIN_LASTNAME=Matter
for var in ADMIN ADMIN_PASSWORD ADMIN_EMAIL ADMIN_FIRSTNAME ADMIN_LASTNAME
do
    sed -i -e "s/^$var=.*/$var=${!var}/" .env
done
export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-"cousins-matter:$curbranch"}
echo "COUSINS_MATTER_IMAGE: $COUSINS_MATTER_IMAGE"

(docker images --format "{{.Repository}}:{{.Tag}}" | grep $COUSINS_MATTER_IMAGE) || error 1 "Image $COUSINS_MATTER_IMAGE not found"

docker compose up -d  # as we did fill the ADMIN_xxx variables in .env, the container will create the superuser
# wait for the containers to start
let max=10
let delay=3
let total_delay=$max*$delay
for i in $(seq 1 $max); do
  sleep $delay
	echo "check all containers are running (#$i/$max)..."
	docker ps -a --filter name=cousins-matter --format '{{.Names}} {{.State}} "{{.Status}}"' | while read -r name state status; do
		if [[ $state != "running" ]]; then
	    echo "#########################################################################################"
  	  echo "# ERROR! $name $status"
    	echo "#########################################################################################"
    	if [[ $i == $max ]]; then
				echo "#########################################################################################"
				echo "# ERROR! Cousins Matter containers are not running properly after $total_delay seconds"
				echo "#########################################################################################"
				docker ps -a --filter name=cousins-matter --format '{{.Names}} {{.State}} "{{.Status}}"'
				exit 1
    	fi
  	fi
	done
done
docker compose down -v
rm -rf "$tmpdir"
echo "test install passed"