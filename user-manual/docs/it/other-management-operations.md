# Altre operazioni di gestione

## Aggiornare Cousins Matter
### In produzione
Scarica l'immagine più recente e riavvia il container
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Ricostruire l'immagine dai sorgenti
Vedi come compilare dai sorgenti per la prima volta [qui](installation.md#compilare-dai-sorgenti).
Per aggiornare la tua immagine dai sorgenti, esegui semplicemente:
```
git pull        # aggiorna i sorgenti
uv sync         # sincronizza le dipendenze
make build      # costruisce l'immagine
make up         # riavvia i servizi (ricostruisce l'immagine prima di riavviare)
# in alternativa all'ultima riga:
make up4run     # riavvia gli altri servizi, ma non cousins-matter
make run        # avvia solo cousins-matter fuori da docker (utile per il debug)
```

## Ruotare la tua chiave segreta
Di tanto in tanto (per esempio una volta al mese), dovresti ruotare la chiave segreta di Cousins Matter. Per farlo, esegui il comando seguente:

```
./manage_cousins_matter.sh rotate-secrets
```

Questo comando ruoterà la chiave segreta e aggiornerà PREVIOUS_SECRET_KEYS nel file .env.

Poiché Cousins Matter non può cambiare da solo la propria chiave segreta, dovrai riavviare i container di Cousins Matter per applicare la nuova chiave segreta.

Per farlo, esegui il comando seguente:

```
docker compose up -d --force-recreate
```
