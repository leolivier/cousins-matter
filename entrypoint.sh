#!/bin/bash
export APP_DIR=/app
. ./prepare-envt.sh || exit 1
# add write access to /app to www-data for redis
setfacl -m u:www-data:w /app
echo "starting $@"   # as provided in the Dockerfile
exec "$@"
