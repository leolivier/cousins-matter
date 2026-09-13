# Impostazioni

## Introduzione

Le impostazioni di Cousins Matter possono essere gestite usando un file `.env` nella directory principale dell'applicazione.

Se hai usato lo script manage_cousins_matter.py per installare Cousins Matter come descritto in [Installazione](installation.md), un file .env di esempio è stato scaricato automaticamente per te e la SECRET_KEY e la POSTGRES_PASSWORD sono state generate automaticamente (**non sovrascriverle!**).

Se lavori dai sorgenti, copia il file `.env.example` in `.env`

In entrambi i casi, devi ora modificare `.env` per impostare le proprietà in base al tuo contesto, come descritto più avanti.

Sono disponibili molte impostazioni per personalizzare la parte tecnica del tuo sito...

Inoltre, non dimenticare di consultare [Personalizzazione](customizing.md) per personalizzare l'aspetto del tuo sito.

**ATTENZIONE**: se il container è già in esecuzione, l'aggiornamento delle impostazioni nel .env non verrà preso in carico finché non lo riavvii.
Per farlo, esegui semplicemente il comando seguente (nella directory del sito):
```
docker compose restart
```

## Sicurezza

* `SECRET_KEY`: una chiave segreta che protegge il tuo sito. Deve essere estremamente complessa e tenuta segreta! Il modo più semplice per generarla è eseguire `python manage_cousins_matter.py rotate-secrets`. Questo script aggiornerà anche PREVIOUS_SECRET_KEYS nel file .env. Questa variabile è usata per decodificare i token che sono stati inviati ai membri con la chiave segreta precedente.

	_(Anche in questo caso, se hai usato manage_cousins_matter.py per installare Cousins Matter, è già stata generata per te, non sovrascriverla)_
* `MAX_REGISTRATION_AGE`: validità massima in secondi dei token di invito, il valore predefinito è 2 giorni (2*24*3600)

## Superuser

Prima di eseguire `docker compose up -d` per la prima volta, fornisci le informazioni per creare il superuser (cioè l'account amministratore).

* `ADMIN`: il nome dell'account superuser
* `ADMIN_PASSWORD`: la password del superuser
* `ADMIN_EMAIL`: l'email del superuser
* `ADMIN_FIRSTNAME`: il nome del superuser
* `ADMIN_LASTNAME`: il cognome del superuser

**TUTTE QUESTE VARIABILI SONO OBBLIGATORIE PER CREARE L'ACCOUNT SUPERUSER E NON HANNO VALORI PREDEFINITI**

## Gestione delle funzionalità

Puoi gestire le funzionalità che verranno offerte ai membri nel file .env.
Per farlo, modifica la variabile FEATURES_FLAGS partendo dal contenuto del file .env.example e imposta a false il valore di ogni funzionalità da ignorare.

Il valore predefinito di FEATURES_FLAGS è:
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True;show_public_chats=True;show_private_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_site_stats=True;show_export_members=True;show_change_language=True;show_genealogy=True"
```

**Flag di funzionalità disponibili:**

* `show_birthdays_in_homepage`: mostra i prossimi compleanni nella homepage per i membri autenticati
* `show_galleries`: attiva la funzionalità di gallerie fotografiche e video
* `show_forums`: attiva le discussioni nel forum
* `show_public_chats`: attiva le stanze di chat pubbliche
* `show_private_chats`: attiva le stanze di chat private
* `show_classified_ads`: attiva la funzionalità di annunci
* `show_polls`: attiva la funzionalità di sondaggi
* `show_event_planners`: attiva le indagini di pianificazione eventi (sondaggi di scelta della data)
* `show_pages`: attiva la funzionalità di pagine CMS
* `show_treasures`: attiva la funzionalità dei tesori (tesori familiari)
* `show_site_stats`: mostra la pagina delle statistiche del sito
* `show_export_members`: consente l'esportazione dell'elenco dei membri in PDF
* `show_change_language`: consente il cambio di lingua nell'interfaccia
* `show_genealogy`: attiva le funzionalità di genealogia (alberi familiari, import/export GEDCOM)

**AVVERTENZE:**

1. La variabile INCLUDE_BIRTHDAYS_IN_HOMEPAGE è stata sostituita dal flag show_birthdays_in_homepage, come mostrato sopra.
2. FEATURES_FLAGS deve rimanere su una sola riga nel file .env. Tutti i flag sono separati da punti e virgola. Se imposti questa variabile nel tuo file .env e un flag non è presente nell'elenco, viene considerato false.

## Personalizzazione generale

### Sito

* `SITE_NAME`: il nome del sito, il valore predefinito è 'Cousins Matter!'.
* `SITE_DOMAIN`: il dominio del sito, ad esempio myfamily.com, nessun valore predefinito.
* `SITE_FOOTER`: il piè di pagina facoltativo del sito, ad esempio "The Simpsons Family Social Network".
* `SITE_LOGO`: l'URL relativo facoltativo del logo del tuo sito (nell'angolo in alto a sinistra). Deve avere un rapporto 4:1. **DEVE ESSERE CONSERVATO IN** nella cartella media/public del tuo sito, quindi **l'URL deve iniziare con '/media/public'** (ad esempio SITE_LOGO='/media/public/my-own-logo.jpg')
* `SITE_COPYRIGHT`: il copyright del tuo sito, ad esempio 'Copyright © 2024 Cousins Matter'.
* `DARK_MODE`: attiva il tema scuro. Il valore predefinito è False.

### Membri

* `ALLOW_MEMBERS_TO_CREATE_MEMBERS`: il valore predefinito è True. Per impedire ai membri di creare e gestire altri membri, imposta a False e solo gli admin potranno farlo.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS`: il valore predefinito è True. Per impedire ai membri di invitare altri membri a iscriversi al sito, imposta a False e solo gli admin potranno farlo.
* `BIRTHDAY_DAYS`: numero di giorni nel futuro per cui mostrare i compleanni, il valore predefinito è 50
* ~~`INCLUDE_BIRTHDAYS_IN_HOMEPAGE`~~: **OBSOLETO** - usa invece `show_birthdays_in_homepage` in `FEATURES_FLAGS`
* `PDF_SIZE`: formato pagina PDF per l'elenco stampato. Formato 'A4' o 'letter'. Il valore predefinito è A4.
* `MAX_CSV_FILE_SIZE`(*): dimensione massima del file CSV di importazione dei membri, il valore predefinito è 2MB.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP`: inserisci qui l'IP esterno del tuo server. È usato per la tracciatura degli accessi quando il login proviene dalla rete interna. Il valore predefinito è "8.8.8.8".
* `LOGIN_HISTORY_PURGE_DAYS`: numero di giorni di conservazione della cronologia degli accessi (visibile agli amministratori nella Django admin), il valore predefinito è 365.

### Gallerie

* `DEFAULT_GALLERY_PAGE_SIZE`: numero di foto per pagina di galleria (modificabile a schermo), il valore predefinito è 25
* `MAX_PHOTO_FILE_SIZE`(*): dimensione massima di ogni foto, il valore predefinito è 5MB
* `MAX_VIDEO_FILE_SIZE`(*): dimensione massima di ogni video, il valore predefinito è 20MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): dimensione massima del file zip di caricamento in blocco delle gallerie, il valore predefinito è 20MB
* `SLIDESHOW_DELAY`: ritardo in secondi tra una foto e l'altra in una presentazione, il valore predefinito è 5

### Messaggi e chat

* `MESSAGE_MAX_SIZE`(*): dimensione massima di un messaggio nel Forum o nelle chat (nota che può contenere una foto), il valore predefinito è 2.5MB.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): dimensione massima di un commento associato a un messaggio nel Forum o nelle chat, il valore predefinito è 1000
* `CONTACT_MAX_SIZE`(*): dimensione massima di un messaggio di contatto, il valore predefinito è 1MB

### Pagine

* `PAGE_MAX_SIZE`(*): dimensione massima di una pagina statica, il valore predefinito è 10MB

### Sondaggi

* `POLL_MAX_SIZE`(*): dimensione massima di un sondaggio, il valore predefinito è 1MB

### Annunci

* `CLASSIFIED_AD_MAX_SIZE`(*): dimensione massima di un annuncio, il valore predefinito è 1MB

### Tesori

* `TROVE_FILE_MAX_SIZE`(*): dimensione massima di un file di un tesoro, il valore predefinito è 20MB
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): dimensione massima di un'immagine di un tesoro, il valore predefinito è 5MB
* `TROVE_THUMBNAIL_SIZE`(*): dimensione massima in pixel di una miniature di un tesoro, il valore predefinito è 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): numero predefinito di tesori per pagina, il valore predefinito è 10

### Annunci

* `MAX_PHOTO_PER_AD`: numero massimo di foto per annuncio, il valore predefinito è 10

### Genealogia

* `FAMILY_CHART_GENERATIONS`: numero di generazioni da mostrare sopra e sotto la persona centrale nell'albero familiare, il valore predefinito è 4
* `FAMILY_CHART_ROOT_PERSON_ID`: ID della persona radice predefinita da mostrare nell'albero familiare se non ne viene specificata nessuna, per impostazione predefinita è l'id della prima persona nel database
* `GEDCOM_FILE`: file GEDCOM da usare per l'esportazione della genealogia, il valore predefinito è 'genealogy.ged'

## Autenticazione OAuth/SSO

* `OAUTH_PROVIDERS`: elenco separato da virgole dei provider OAuth da attivare. Provider disponibili: `google`, `facebook`, `apple`, `github`, `pocketid` o qualsiasi provider `openid_connect`. Il valore predefinito è vuoto (OAuth non attivo).
* `SOCIALACCOUNT_AUTO_SIGNUP`: se richiedere la conferma quando un utente accede con un provider OAuth. Il valore predefinito è False (è richiesta la conferma).

Per ogni provider devi impostare:
* `<PROVIDER>_OAUTH_CLIENT_ID`: il client ID OAuth del provider
* `<PROVIDER>_OAUTH_CLIENT_SECRET`: il client secret OAuth del provider

Per i provider OpenID Connect (incluso PocketID):
* `<PROVIDER>_SERVER_URL`: l'URL del server OpenID Connect

**Esempio di configurazione:**
```
OAUTH_PROVIDERS=google,github,pocketid
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

Vedi [Autenticazione OAuth](oauth-authentication.md) per le istruzioni di configurazione dettagliate di ogni provider.

## Livelli di log

* `DJANGO_LOG_LEVEL`: livello di log per django e le librerie interne, il valore predefinito è INFO
* `CM_LOG_LEVEL`: livello di log per cousins matter, il valore predefinito è INFO

## Configurazione di rete

* `ALLOWED_HOSTS`: elenco separato da virgole degli host. Il valore predefinito è '127.0.0.1,localhost,<SITE_DOMAIN\>'. __Devi impostare ALLOWED_HOSTS per la produzione__ e __DEVE__ contenere l'URL completo del tuo sito e, a volte, a seconda delle impostazioni di rete del tuo host, l'IP generale del sito, ad esempio:

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: elenco separato da virgole degli host. Il valore predefinito è vuoto.

	__ATTENZIONE!__ Se il tuo log mostra errori come

	`Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

	devi impostare `CORS_ALLOWED_ORIGINS=<your full domain>` (ad esempio https://my.cousins-matter.com) nel file `.env`,

	__Non usare la sintassi Python mostrata nell'errore!__.

	Se hai più host, elencali separati da virgole, ad esempio

	`CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

	Per tua informazione, `CSRF_TRUSTED_ORIGINS` è impostato sul valore di `CORS_ALLOWED_ORIGINS`

## Internazionalizzazione

* `LANGUAGE_CODE`: ad esempio 'fr' o 'fr-CA'. Il valore predefinito è 'en-US'.
* `TIME_ZONE`: fuso orario, il valore predefinito è 'Europe/Paris'.

## Proprietà email

* `EMAIL_HOST`: nome host SMTP, nessun valore predefinito
* `EMAIL_PORT`: porta a cui connettersi sul server SMTP
* `EMAIL_USE_TLS`: il server SMTP usa STARTLS se true, il valore predefinito è true
* `EMAIL_USE_SSL`: il server SMTP usa SSL se true, il valore predefinito è false
* `EMAIL_HOST_USER`: nome utente per connettersi al server SMTP.
* `EMAIL_HOST_PASSWORD`: password per la connessione al server SMTP
* `DEFAULT_FROM_EMAIL`: indirizzo email predefinito da usare per l'invio delle email

## Database

* `POSTGRES_USER`: l'utente postgres, il valore predefinito è 'cousinsmatter'
* `POSTGRES_PASSWORD`: la password di postgres. Viene generata automaticamente se usi manage_cousins_matter.py per installare o migrare Cousins Matter. __ATTENZIONE!__ Usa solo -_./* come caratteri speciali se vuoi cambiarla. Evita assolutamente : e @ !
* `POSTGRES_DB`: il database postgres, il valore predefinito è 'cousinsmatter'
* `POSTGRES_HOST`: l'host postgres, il valore predefinito è 'postgres'

* `REDIS_HOST`: l'host redis, il valore predefinito è 'redis'

## Altre archiviazioni dei media

* `MEDIA_STORAGE` e `MEDIA_STORAGE_OPTIONS`: vedi [Archiviazione dei media](/media-storage.md)

## NOTE

__(*) ATTENZIONE:__ se vuoi cambiare una delle variabili che controllano la dimensione di ciò che può essere caricato e stai usando il reverse proxy nginx, verifica il valore di `client_max_body_size` in config/nginx/nginx.conf affinché resti superiore alle variabili di dimensione che cambi sopra. Altrimenti riceverai un errore 413 da Nginx. Il valore predefinito fornito è elevato (20MB) ma potrebbe essere necessario aumentarlo per supportare video più grandi.
