# Weitere Verwaltungsoperationen

## Cousins Matter aktualisieren
### In der Produktivumgebung
Ziehen Sie das neueste Image und starten Sie den Container neu
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Image aus dem Quellcode neu bauen
Wie Sie zum ersten Mal aus dem Quellcode bauen, sehen Sie [hier](installation.md#build-aus-dem-quellcode).
Um Ihr Image aus dem Quellcode zu aktualisieren, führen Sie einfach aus:
```
git pull        # refresh sources
uv sync         # sync dependencies
make build      # build the image
make up         # restart the services (this rebuild the image before restarting)
# alternatively to the last line:
make up4run     # restart the other services, but cousins-matter
make run        # start cousins-matter only outside docker (useful for debugging)
```

## Ihren Secret Key rotieren
Von Zeit zu Zeit (z. B. einmal im Monat) sollten Sie den Secret Key von Cousins Matter rotieren. Führen Sie dazu den folgenden Befehl aus:

```
./manage_cousins_matter.sh rotate-secrets
```

Dieser Befehl rotiert den Secret Key und aktualisiert PREVIOUS_SECRET_KEYS in der .env-Datei.

Da Cousins Matter seinen Secret Key nicht selbst ändern kann, müssen Sie die Cousins-Matter-Container neu starten, um den neuen Secret Key anzuwenden.

Führen Sie dazu den folgenden Befehl aus:

```
docker compose up -d --force-recreate
```
