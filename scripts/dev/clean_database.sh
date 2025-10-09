#!/bin/bash

# a script for cleaning the migrations, removing the database and restarting fresh
# from https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html
#set -x

if [[ ! -d ./data/postgres ]];
then echo "no postegres database directory in the data directory, please make sure first you are in the project directory before running this script";
     exit 1
fi;
if [[ ! -f ./manage.py ]];
then echo "This does not look like a django project";
     exit 2
fi;
read -p "Are you sure you want to delete the database and start fresh? [y/N] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]];
then
	rm -rf ./data/postgres
	docker compose up -d postgres
	python manage.py makemigrations
	python manage.py migrate
	/app/scripts/create_superuser.sh
fi;
