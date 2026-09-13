# Other management operations

## Upgrade Cousins Matter
### In production
Pull the latest image and restart the container
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Rebuild image from source
See how to build from source for the 1rst time [here](installation.md#build-from-source).
To update your image from source, just do:
```
git pull        # refresh sources
uv sync         # sync dependencies
make build      # build the image
make up         # restart the services (this rebuild the image before restarting)
# alternatively to the last line:
make up4run     # restart the other services, but cousins-matter
make run        # start cousins-matter only outside docker (useful for debugging)
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
