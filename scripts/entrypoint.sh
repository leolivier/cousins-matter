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
if [ ! -f /app/data/db.sqlite3 ]; then  # 1rst run
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
  ADMIN=$(get_env ADMIN)
  ADMIN_PASSWORD=$(get_env ADMIN_PASSWORD)
  ADMIN_EMAIL=$(get_env ADMIN_EMAIL)
	ADMIN_FIRSTNAME=$(get_env ADMIN_FIRSTNAME)
	ADMIN_LASTNAME=$(get_env ADMIN_LASTNAME)

  if [[ -z $ADMIN || -z $ADMIN_PASSWORD || -z $ADMIN_EMAIL ]]; then
    echo "ADMIN, ADMIN_PASSWORD or ADMIN_EMAIL is not set, the superuser won't be created."
    echo "Run 'python manage.py createsuperuser' through docker exec to create it after the container is started."
  else
		if [[ -z $ADMIN_FIRSTNAME ]]; then
		  ADMIN_FIRSTNAME="Cousins"
		fi
		if [[ -z $ADMIN_LASTNAME ]]; then
		  ADMIN_LASTNAME="Matter"
		fi
    echo "creating superuser..."
    cmd="from members.models import Member; Member.objects.create_superuser(username='$ADMIN', email='$ADMIN_EMAIL', password='$ADMIN_PASSWORD', first_name='$ADMIN_FIRSTNAME', last_name='$ADMIN_LASTNAME')"
    echo $cmd
    sudo -u $USER python manage.py shell -c "$cmd"
  fi 
fi

sudo -u $USER python manage.py check

echo "environment is ready..."


echo "starting $@"   # as provided in the Dockerfile
exec "$@"	
