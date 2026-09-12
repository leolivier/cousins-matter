# Archiviazione dei media

## AVVERTENZE

* __Questa è attualmente una funzionalità <span class="blinking-text"><u>BETA</u></span>!__
* __Queste impostazioni sono più complesse e sono <u>riservate agli utenti avanzati</u>.__

## Archiviazione dei media predefinita

Per impostazione predefinita, i media sono conservati nella sottodirectory 'media' nello stesso file system di Cousins Matter.

È una soluzione molto semplice, ma ha alcuni inconvenienti, in particolare sul piano della sicurezza, come spiegato in [questo articolo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Altri sistemi di archiviazione dei media

Cousins Matter supporta anche le archiviazioni media S3 usando il pacchetto 'django-storages'. Per configurare una tale archiviazione, devi semplicemente definire due nuove variabili nel tuo file .env: MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS.

**Solo l'archiviazione Cloudflare R2 è stata testata e sperimentata finora** ma le altre archiviazioni S3 dovrebbero funzionare purché tu trovi la configurazione giusta. Vedi [Altre archiviazioni compatibili S3](#other-s3-compatible-storages) più avanti.

Se riesci a creare una configurazione funzionante per un'archiviazione non testata, crea per favore una Pull Request su GitHub su questa pagina per spiegare come funziona.

### Cloudflare R2

Per usare Cloudflare R2, ovviamente devi prima [creare un account su Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Poi devi [creare un bucket S3 su Cloudflare R2 - scheda Dashbord](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Ricorda il nome del bucket.

Devi anche [creare un token applicazione](https://developers.cloudflare.com/r2/api/tokens/). Ricorda la access key, la secret key e gli URL degli endpoint mostrati nell'ultima pagina quando il tuo token API viene creato.

Fatto questo, la configurazione nel tuo file .env dovrebbe essere simile a questa:
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS='{"access_key":"<your access key>","secret_key":"<your secret key>","bucket_name":"<your bucket name>","endpoint_url":"https://<your account id>.r2.cloudflarestorage.com"}'
```

Poi riavvia Cousins Matter: `docker compose restart cousins-matter`

#### Altre archiviazioni compatibili S3

La configurazione delle altre archiviazioni compatibili S3 (incluso AWS S3, l'originale) dovrebbe essere simile a quella di R2 ma non è ancora stata testata.

Dai un'occhiata alla [documentazione di django-storages](https://django-storages.readthedocs.io/en/latest/index.html) per vedere quali variabili specifiche vanno impostate nelle opzioni per il tuo caso particolare.


## Migrazione dalla directory media a un'archiviazione S3 esterna

Puoi usare a questo scopo gli strumenti di archiviazione S3. Per esempio, su AWS S3, puoi usare

```
$ aws s3 sync ./media s3://YOUR_BUCKET/media/
```

__CONSIGLIO__: Qualunque sia il tuo provider S3, usare [rclone](https://rclone.org/install/) fa risparmiare molto tempo per migrare i file verso il tuo nuovo backend. Prima crea una configurazione per il tuo backend (`rclone config`), poi copia i tuoi file media: `rclone copy ./media <your backend>:<your root>`
