#!/bin/bash
export APP_DIR=/app
. ./prepare-envt.sh || exit 1
echo "starting $@"   # as provided in the Dockerfile
exec "$@"
