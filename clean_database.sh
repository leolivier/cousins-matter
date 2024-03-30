#!/bin/bash

# a script for cleaning the migrations, removing the database and restarting fresh
# from https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html
#set -x

if [[ ! -f ./db.sqlite3 ]];
then echo "no db.sqlite3 in the current directory, please make sure first you are in the project directory before running this script";
     exit 1
fi;
if [[ ! -f ./manage.py ]];
then echo "This does not look like a django project";
     exit 1
fi;
# if [[ -z $DJANGO_SUPERUSER_PASSWORD]];
# then echo "DJANGO_SUPERUSER_PASSWORD is not set, please set it before running this script";
# 		 exit 1
# fi;
read -p "Are you sure you want to delete the database and start fresh? [y/N] " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]];
then
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc"  -delete

	rm db.sqlite3

	python manage.py makemigrations
	python manage.py migrate

	# recreate the superuser
	echo "creating superuser"
	python manage.py createsuperuser
fi;