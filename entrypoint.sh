#!/bin/sh
LIGHTTPD_PORT=${LIGHTTPD_PORT:=8001}
DJANGO_PORT=${DJANGO_PORT:=8000}

echo "collecting statics..."
python manage.py collectstatic --no-input
echo "migrating the database..."
python manage.py migrate

# start the server using daphne in background mode on a socket
#daphne -b 0.0.0.0 -p 8000 cousinsmatter.asgi:application
echo "starting daphne..."
daphne -u /var/run/cousinsmatter.socket cousinsmatter.asgi:application &

echo "starting lighttpd..."
exec lighttpd -D -f lighttpd.conf


