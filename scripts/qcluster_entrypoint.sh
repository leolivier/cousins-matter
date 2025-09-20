#!/bin/bash

echo "Running qcluster entrypoint.sh as $USER..."
set -x
/app/scripts/init_envt.sh || exit $?

echo "starting django-q cluster"
exec python manage.py qcluster
