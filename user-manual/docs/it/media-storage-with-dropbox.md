# AVVERTENZA ⚠️ AL MOMENTO È SUPPORTATO SOLO S3, DROPBOX NON FUNZIONA (probabilmente a causa di un problema di django-storages)


# Archiviazione dei media

## AVVERTENZE

* __Questa è attualmente una funzionalità <span class="blinking-text"><u>BETA</u></span>!__
* __Queste impostazioni sono più complesse e sono <u>riservate agli utenti avanzati</u>.__

## Archiviazione dei media predefinita
Per impostazione predefinita, i media sono conservati nella sottodirectory 'media' nello stesso file system di Cousins Matter.

È una soluzione molto semplice, ma ha alcuni inconvenienti, in particolare sul piano della sicurezza, come spiegato in [questo articolo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Altri sistemi di archiviazione dei media

Cousins Matter supporta anche tutta una serie di altre archiviazioni media usando il pacchetto 'django-storages'. Per configurare una tale archiviazione, devi semplicemente definire due nuove variabili nel tuo file .env: MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS.

Le archiviazioni media supportate da django-storages al momento della stesura di questa pagina sono:

* Amazon S3
* Apache Libcloud
* Azure Storage
* Dropbox
* FTP
* Google Cloud Storage
* SFTP
* S3 Compatible
	* Backblaze B2
	* Cloudflare R2
	* Digital Ocean
	* Oracle Cloud
	* Scaleway

**Solo l'archiviazione Dropbox e l'archiviazione Cloudflare R2 sono state testate e sperimentate finora** ma tutte le altre archiviazioni dovrebbero funzionare purché tu trovi la configurazione giusta. Vedi [Altre archiviazioni compatibili S3](#other-s3-compatible-storages) e [Archiviazioni non testate](#non-tested-storages) più avanti.

Se riesci a creare una configurazione funzionante per un'archiviazione non testata, crea per favore una Pull Request su GitHub su questo file per spiegare come funziona.

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
Poiché tutti questi backend condividono la stessa implementazione, non hai bisogno di creare la tua immagine come descritto per le [archiviazioni non testate](#non-tested-storages) più avanti.
Dai un'occhiata alla [documentazione di django-storages](https://django-storages.readthedocs.io/en/latest/index.html) per vedere quali variabili specifiche vanno impostate nelle opzioni per il tuo caso particolare.

### Dropbox

Ti serve un account Dropbox per usare questa archiviazione (vedi https://www.dropbox.com/register).
Poi devi [creare un'applicazione](https://www.dropbox.com/developers/apps). Il modulo delle impostazioni dovrebbe apparire così:
![creazione app dropbox](assets/create_dropbox_app.webp). Ricorda l'app key e l'app secret.
Vai alla scheda Permissions e compila il modulo così:
![permessi app dropbox](assets/dropbox_app_permissions.webp)
Non dimenticare di cliccare su Submit alla fine...

Poi, come descritto nella [pagina Dropbox di Django-storages](https://django-storages.readthedocs.io/en/latest/backends/dropbox.html), ottieni il tuo codice di autorizzazione e, usando questo codice, ottieni l'access_token (che inizia con "sl.") e il refresh token.

Fatto questo, la configurazione nel tuo file .env dovrebbe essere simile a questa:

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS='{"app_key":"<your app key>","app_secret":"<your app secret>","root_path":"/","oauth2_access_token":"<your access token>","oauth2_refresh_token":"<your refresh token>"}'
```

## Archiviazioni non testate

### Installare il pacchetto Python necessario

**Nota:** questo non è necessario per tutti i backend compatibili S3, vedi sopra [Altre archiviazioni compatibili S3](#other-s3-compatible-storages)

Prima di tutto, devi installare un pacchetto python specifico che implementa il collegamento al tuo backend.

Vedi la pagina relativa al tuo backend nella [documentazione di django-storages](https://django-storages.readthedocs.io/en/latest/index.html) per conoscere il nome del tuo pacchetto, che dovrebbe apparire come `pip install django-storages[<backend name>]`. Ricorda il valore di `<backend name>`, ti servirà per sostituirlo più avanti.

Ci sono due modi per installare questo pacchetto, usa il metodo che preferisci...

* Da un lato puoi creare la tua immagine di Cousins Matter derivata da quella ufficiale, così:
	1. crea un Dockerfile in questo modo:

		```
		FROM ghcr.io/leolivier/cousins-matter:latest
		RUN pip install django-storages[<backend name>]
		```

	1. costruisci la nuova immagine (cambia il tag dell'immagine come preferisci):

		```
		docker build -t cousins-matter:local .
		```

	1. imposta COUSINS_MATTER_IMAGE nel tuo file .env in modo che punti a `cousins-matter:local` (o al tuo tag se l'hai cambiato)
	1. ricrea i container

		```
		docker compose up -d --force-recreate cousins-matter qcluster
		```

	Dovrai ricostruire l'immagine e ricreare i container ogni volta che viene rilasciata una nuova versione.

* Oppure aggiorni i container in esecuzione così:

	```
	docker exec -it cousins-matter pip install django-storages[<backend name>]
	docker exec -it cousins-matter.qcluster pip install django-storages[<backend name>]
	```

	Dovrai eseguire questi 2 comandi ogni volta che i tuoi container vengono aggiornati con una nuova immagine ufficiale.

__AVVERTENZA__: in alcuni casi c'è più di un pacchetto da installare. Per esempio, se usi Azure Storage con Managed Identity, dovrai installare un altro pacchetto per Managed Identity. Procedi come descritto sopra e aggiungi semplicemente i nomi degli altri pacchetti alla fine della riga di comando `pip install`

### Creare la configurazione

Dai un'occhiata alle configurazioni riportate sopra per [Dropbox](#dropbox) e [Cloudflare R2](#cloudflare-r2) per capire come funzionano le 2 variabili MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS e consulta la [documentazione di django-storages](https://django-storages.readthedocs.io/en/latest/index.html) per il tuo backend, in modo da adattare queste configurazioni al tuo caso.

MEDIA_STORAGE deve essere preso dalla pagina del tuo backend. Usa il valore di BACKEND nel blocco STORAGES (ad esempio storages.backends.azure_storage.AzureStorage per il backend Azure Storage).

MEDIA_STORAGE_OPTIONS deve rimanere su una sola riga. Ha il formato seguente (l'ordine degli apici singoli e doppi è importante!)

```
MEDIA_STORAGE_OPTIONS='{"option1":"value1","option2":"value2",...}'
```

Sostituisci option1, option2 con le variabili in minuscolo descritte nella documentazione e con i loro valori per il tuo caso.

## Migrazione dalla directory media a un'archiviazione esterna

__CONSIGLIO__: se hai già salvato molti file nella tua directory media, usare [rclone](https://rclone.org/install/) fa risparmiare molto tempo per migrare i file verso il tuo nuovo backend. Prima crea una configurazione per il tuo backend (`rclone config`), poi copia i tuoi file media: `rclone copy ./media <your backend>:<your root>`
