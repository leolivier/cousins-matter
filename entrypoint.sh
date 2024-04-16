#!/bin/sh
LIGHTTPD_PORT=${LIGHTTPD_PORT:=8001}
DJANGO_PORT=${DJANGO_PORT:=8000}

echo "collecting statics..."
python manage.py collectstatic --no-input
echo "migrating the database..."
python manage.py migrate

mkdir -p /var/log/supervisord /var/run/supervisord
# starting the supervisord provided in the Dockerfile
exec "$@"
