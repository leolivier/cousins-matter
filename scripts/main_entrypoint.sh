#!/bin/bash

echo "Running main entrypoint.sh as $USER..."
set -x
/app/scripts/init_envt.sh || exit $?


echo "starting $@"   # as provided in the Dockerfile
exec "$@"	
