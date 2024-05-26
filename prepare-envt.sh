export LIGHTTPD_PORT=${LIGHTTPD_PORT:=8001}
export DJANGO_PORT=${DJANGO_PORT:=8000}

if [ ! -f template.lighttpd.conf ];
then echo "Must be run from the cousins-matter directory!"
     exit 1;
fi

for file in lighttpd.conf supervisord.conf
do cat template.$file | sed -e "s,{%APP_DIR%},$APP_DIR,g" > $file
done

echo "collecting statics..."
python manage.py collectstatic --no-input
echo "migrating the database..."
python manage.py migrate
python manage.py check

sudo=''
if [[ -n "$EUID" && $EUID -ne 0 ]];
then sudo='sudo'
fi
$sudo mkdir -p "/var/log/supervisord" "/var/run/supervisord"
