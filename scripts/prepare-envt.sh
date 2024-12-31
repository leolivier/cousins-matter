export LIGHTTPD_PORT=${LIGHTTPD_PORT:=8001}
export DJANGO_PORT=${DJANGO_PORT:=8000}

if [ ! -f template.lighttpd.conf ];
then echo "Must be run from the cousins-matter directory!"
     exit 1;
fi

for file in lighttpd.conf supervisord.conf
do cat template.$file | sed -e "s,{%APP_DIR%},$APP_DIR,g;s,{%USER%},$USER,g" > $file
done
chown -R $USER:$USER media  # make sure the media directory is owned by the cm_user
echo "collecting statics..."
sudo -u $USER python manage.py collectstatic --no-input
echo "migrating the database..."
sudo -u $USER python manage.py migrate
sudo -u $USER python manage.py check

echo "environment is ready..."
