#!/bin/bash
. ./scripts/prepare-envt.sh || exit 1
echo "Starting cron..."
cron
echo "starting $@"   # as provided in the Dockerfile
exec "$@"	
