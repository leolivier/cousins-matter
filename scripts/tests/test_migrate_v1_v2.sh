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

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)
unzip -q "$script_dir/tests/resources/cm-v1-tests.zip" -d "$tmpdir"
cd $tmpdir
# .env was existing before migration
[[ ! -f .env ]] && error 1 "No .env file found in $tmpdir"
# no need to set the superuser variables as the superuser must already exist in tha database
# the postgres password is added by the migration tool
# use the local build if not provided
export COUSINS_MATTER_IMAGE=${COUSINS_MATTER_IMAGE:-"cousins-matter:$curbranch"}
echo "COUSINS_MATTER_IMAGE: $COUSINS_MATTER_IMAGE"

python "$script_dir/manage_cousins_matter.py" migrate-v1-v2 -d "$tmpdir" -b "$curbranch"
[[ $? != 0 ]] && error 1 "manage_cousins_matter failed to migrate from v1 to v2"

(docker images --format "{{.Repository}}:{{.Tag}}" | grep $COUSINS_MATTER_IMAGE) || error 1 "Image $COUSINS_MATTER_IMAGE not found"

docker compose up -d
# wait for the containers to start
let max=10
let min_ok=5
let delay=3
let total_delay=$max*$delay
nb_ok=0
for i in $(seq 1 $max); do
  sleep $delay
	echo "check all containers are running (#$i/$max)..."
	nb_ok=$(($nb_ok + 1))
	docker ps -a --filter name=cousins-matter --format '{{.Names}} {{.State}} "{{.Status}}"' | while read -r name state status; do
		if [[ $state != "running" ]]; then
		  nb_ok=0
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
	echo "nb_ok: $nb_ok"
	if [[ $nb_ok == $min_ok ]]; then
		echo "#########################################################################################"
		echo "# Cousins Matter containers has been running properly during $((nb_ok * delay)) seconds"
		echo "#########################################################################################"
		break
	fi
done
# copy the sqlite database to a directory mounted in the container (data does not exist anymore in the container)
cp data/db.sqlite3 media/public/db.sqlite3
docker exec "cousins-matter" python -m scripts.tests.check_after_migration
rm media/public/db.sqlite3
docker compose down -v
cd ..
sudo rm -rf "$tmpdir"
echo "test migrate v1 to v2 passed"