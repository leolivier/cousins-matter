#!/bin/bash

# Test rotating secrets in .env
error() {
	code=$1
	shift
  echo "Error: $@" >&2
  exit $code
}
get_key() {
	key=$1
	cat .env | grep -e "^${key}=" | cut -d= -f2 | sed -E 's/^"([^"]*)".*$/&1/;'"s/^'([^']*)'.*$/\1/"
}

set -e
[[ -f .env ]] || error 1 "No .env file found in $PWD"
old_secret=$(get_key SECRET_KEY)
old_prev_secret=$(get_key PREVIOUS_SECRET_KEYS)
[[ -z $old_secret ]] && error 1 "No old secret found in $PWD/.env"
grep -q "^PREVIOUS_SECRET_KEYS=" .env || error 1 "No old previous secret found in $PWD/.env"
# Create a temporary directory
tmp_dir=$(mktemp -d)
# Copy the .env file from the project directory
cp .env $tmp_dir
script_dir=$(cd $(dirname $0); cd ..; pwd)
cd $tmp_dir
# Run the rotate_secret script
$script_dir/manage_cousins_matter.py rotate-secrets
new_secret=$(get_key SECRET_KEY)
new_prev_secret=$(get_key PREVIOUS_SECRET_KEYS)
# Check if the secrets have been rotated
[[ -z $new_secret || -z $new_prev_secret ]] && error 1 "Secrets have not been rotated"
[[ $new_secret == $old_secret ]] && error 2 "New secret is the same as old secret"
[[ $new_prev_secret == $old_prev_secret ]] && error 3 "New previous secret is the same as old previous secret"
[[ ${new_prev_secret} =~ "${old_secret}"$ ]] || error 4 "Old secret is not in the list of new previous secrets"
cd
rm -rf $tmp_dir
echo "test rotate_secret passed"
exit 0