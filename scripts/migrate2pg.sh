#!/bin/bash

# a script for migrating the database from sqlite to postgres

set -e

if [[ ! -d ./data || ! -f ./data/db.sqlite3 ]];
then echo "no data directory or no db.sqlite3 in the data directory, please make sure first you are in the project directory before running this script";
     exit 1
fi;
if [[ ! -f ./manage.py ]];
then echo "This does not look like a django project";
     exit 2
fi;
if [[ -d ./data/postgres || -f ./data/postgres ]];
then echo "postgres data directory already exists, please remove it before running this script";
     exit 3
fi;

docker compose -f docker-compose-migrate.yaml up -d postgres
while true; do
	sleep 10
	done=$(docker logs cousins-matter-postgres 2>&1 | grep "database system is ready to accept connections"|wc -l)
	if [[ $done == 2 ]]; then
		docker compose up pgloader
		if [[ $? != 0 ]]; then
			echo "pgloader failed, see error message, try to fix it (usually it's a password issue), then rerun this script"
			sudo rm -rf ./data/postgres
			exit 1
		fi
		docker container rm cousins-matter-pgloader
		break
	fi
done
