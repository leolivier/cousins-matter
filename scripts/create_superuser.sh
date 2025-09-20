#!/bin/bash

if [[ -z $USER ]]; then
	export USER=cm_user
fi

get_env() {
  local key="$1" val
  val=$(grep -m1 -E "^${key}=" /app/.env | cut -d= -f2- || true)
  # if the value begins and ends with the same quotation mark (single or double), it is removed
  if [[ $val =~ ^\".*\"$ ]] || [[ $val =~ ^\'.*\'$ ]]; then
    val=${val:1:-1}
  fi
  printf '%s' "$val"
}

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
	sudo -u cm_user python manage.py shell -c "$cmd"
fi 
