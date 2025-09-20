#!/bin/bash
set -x
init_in_progress=/app/data/init_in_progress
wait_init_and_exit() {
  # wait max for $1 or 10 seconds
  wait=${1:-10}
  for i in {1..$wait}; do
    if [[ ! -d $init_in_progress ]]; then
      exit 0
    fi
    sleep 1
  done
  echo "Init not finished in $wait seconds, exiting..."
  exit 1
}

if ! mkdir -p $init_in_progress; then  # mkdir is atomic
  echo "Another container is already initializing the environment. Waiting..."
  wait_init_and_exit 20
fi
set -e
# make sure the init_in_progress file is removed on exit or signal
cleanup() {
    rm $init_in_progress
}
trap cleanup EXIT INT TERM HUP QUIT

first_run=false
mkdir -p /app/media/avatars && first_run=true  # mkdir is atomic

echo_dot_env() {
    echo "The .env file is missing or not readable."
    echo "Please download .env.example from github latest release, rename it to .env, and fill it with the right data."
    echo "Then use --force-recreate option with 'docker compose up' to recreate the container."
}

if [[ $PWD != '/app' ]]; then
    echo "The container is inconsistent: PWD is not set to /app."
    echo "Please make sure you are in the project directory before running this script."
    exit 1
fi
if [[ ! -f .env || ! -r .env ]]; then
    echo_dot_env
    exit 2
fi

get_env() {
  local key="$1" val
  if grep -m1 -E "^${key}=" /app/.env; then
    val=$(grep -m1 -E "^${key}=" /app/.env | cut -d= -f2- || true)
    # if the value begins and ends with the same quotation mark (single or double), it is removed
    if [[ $val =~ ^\".*\"$ ]] || [[ $val =~ ^\'.*\'$ ]]; then
      val=${val:1:-1}
    fi
    printf '%s' "$val"
  else
    echo "NOT_FOUND"
  fi
}

SECRET_KEY=$(get_env SECRET_KEY)
if [[ -z $SECRET_KEY ]]; then
		echo "Error: SECRET_KEY is not set in the .env file."
		exit 3
fi

if [[ $first_run == true ]]; then
	mkdir -p media/public media/avatars
	touch media/public/theme.css
fi

echo "migrating the database..."
python manage.py migrate --no-input
echo "collecting statics..."
python manage.py collectstatic --no-input

if [[ $first_run == true ]]; then
	/app/scripts/create_superuser.sh
fi

python manage.py check --deploy

echo "environment is ready..."

exit 0
