#!/bin/bash
export APP_DIR=/app
. ./scripts/prepare-envt.sh || exit 1
# add full access to /app to www-data for redis and ligthttpd
setfacl -m u:www-data:rwx /app
echo "starting $@"   # as provided in the Dockerfile
exec "$@"	
