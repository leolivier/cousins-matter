#!/bin/bash
export LIGHTTPD_PORT=${LIGHTTPD_PORT:=8001}
export DJANGO_PORT=${DJANGO_PORT:=8000}

echo "Running entrypoint.sh as $USER..."

if [ ! -f template.lighttpd.conf ]; then 
    echo "Must be run from the cousins-matter directory!"
    exit 1;
fi
if [ -d /app/.env ]; then
    # can happen if the container has 1rst been started w/o a proper .env file mounted
    echo "The container is inconsistent, please use --force-recreate option with 'docker compose up' to recreate it."
    exit 1
fi
if [ ! -f /app/.env ]; then
    echo ".env doesn't exist, please create it by downloading .env.example from github latest release."
    exit 1
fi

SECRET_KEY=$(cat /app/.env | grep 'SECRET_KEY=' | cut -d= -f2)
if [[ -z $SECRET_KEY ]]; then
		echo "Error: SECRET_KEY is not set in the .env file."
		exit 1
fi

first_run=false
if [ ! -f /app/data/postgres ]; then  # 1rst run
  first_run=true
  mkdir -p media/public media/avatars
  chown -R $USER:$USER media data # make sure the media and data directories are owned by the cm_user
  touch media/public/theme.css
fi

for file in lighttpd.conf supervisord.conf	
do cat template.$file | sed -e "s,{%APP_DIR%},$APP_DIR,g;s,{%USER%},$USER,g" > $file
done
echo "migrating the database..."
sudo -u $USER python manage.py migrate
echo "collecting statics..."
sudo -u $USER python manage.py collectstatic --no-input

get_env() {
  local key="$1" val
  val=$(grep -m1 -E "^${key}=" /app/.env | cut -d= -f2- || true)
  # si la valeur commence et finit par le même guillemet (simple ou double), on l'enlève
  if [[ $val =~ ^\".*\"$ ]] || [[ $val =~ ^\'.*\'$ ]]; then
    val=${val:1:-1}
  fi
  printf '%s' "$val"
}

if [[ $first_run == true ]]; then
	/app/scripts/create_superuser.sh
fi

sudo -u $USER python manage.py check

echo "environment is ready..."


echo "starting $@"   # as provided in the Dockerfile
exec "$@"	
