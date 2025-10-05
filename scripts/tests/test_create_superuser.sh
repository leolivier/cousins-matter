#!/bin/bash

# this script is expected to be run from the root of the dev environment project
set -e
curbranch=$(git branch --show-current)
if [[ -z "$curbranch" ]]; then
    echo "Error: git branch --show-current returned an empty string. Please run this script from the root of the dev environment project."
    exit 1
fi
tmpdir=$(mktemp -d)
python -m scripts.install_cousins_matter -d "$tmpdir" -b "$curbranch"
pushd "$tmpdir"
docker compose up -d  # as we didn't fill the ADMIN_xxx variables in .env, the container will fail to create the superuser
# wait for the containers to start
sleep 20
python -m scripts.create_superuser
docker compose down -v
popd
rm -rf "$tmpdir"
echo "test create superuser passed"

