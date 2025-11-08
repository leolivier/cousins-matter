# Other management operations

## Upgrade Cousins Matter
### In production
Pull the latest image and restart the container
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### From source
Refresh sources from github, reinstall packages, migrate the database
```
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Rotate your secret key
From time to time (e.g. once a month), you should rotate the Cousins Matter secret key. To do so, run the following command:

```
./manage_cousins_matter.sh rotate-secrets
```

This command will rotate the secret key and update the PREVIOUS_SECRET_KEYS in the .env file.

As Cousins Matter cannot change itself its secret key, you will need to restart the Cousins Matter containers to apply the new secret key.

To do so, run the following command:

```
docker compose up -d --force-recreate
```
