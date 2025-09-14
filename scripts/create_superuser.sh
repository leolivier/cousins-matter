#!/bin/bash

if [[ -z $USER ]]; then
	USER=cm_user
fi

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
