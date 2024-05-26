#!/bin/bash
export APP_DIR=$PWD
. ./prepare-envt.sh || exit 1
supervisord=$(command -v supervisord)
[ -z "$supervisord" ] && echo "supervisord not found" && exit 1
echo "starting supervisord"
exec sudo $supervisord -c "$APP_DIR/supervisord.conf"
