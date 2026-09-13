# WARNUNG ⚠️ DERZEIT WIRD NUR S3 UNTERSTÜTZT, DROPBOX FUNKTIONIERT NICHT (wahrscheinlich wegen eines Problems mit django-storages)


# Medienspeicher

## WARNUNGEN

* __Dies ist derzeit eine <span class="blinking-text"><u>BETA</u></span>-Funktion!__
* __Diese Einstellungen sind komplexer und <u>fortgeschrittenen Benutzern vorbehalten</u>.__

## Standard-Medienspeicher
Standardmäßig werden die Medien im Unterverzeichnis 'media' im selben Dateisystem wie Cousins Matter gespeichert.

Dies ist sehr einfach, hat aber einige Nachteile, insbesondere im Bereich der Sicherheit, wie in [diesem Artikel](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html) erklärt wird.

## Andere Medienspeicher

Cousins Matter unterstützt auch eine Reihe anderer Medienspeicher mithilfe des Pakets 'django-storages'. Um einen solchen Speicher einzurichten, müssen Sie nur zwei neue Variablen in Ihrer .env-Datei definieren: MEDIA_STORAGE und MEDIA_STORAGE_OPTIONS.

Die von django-storages zum Zeitpunkt der Erstellung dieser Seite unterstützten Medienspeicher sind: 

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

**Bisher wurden nur der Dropbox-Speicher und der Cloudflare-R2-Speicher getestet und erprobt**, aber alle anderen Speicher sollten funktionieren, solange Sie die richtige Konfiguration finden. Siehe [Andere S3-kompatible Speicher](#other-s3-compatible-storages) und [Nicht getestete Speicher](#non-tested-storages) unten.

Wenn Sie eine funktionierende Konfiguration für nicht getestete Speicher erstellen, erstellen Sie bitte einen Pull Request auf GitHub zu dieser Datei, um zu erklären, wie es funktioniert.

### Cloudflare R2

Um Cloudflare R2 zu verwenden, müssen Sie natürlich zuerst [ein Konto bei Cloudflare anlegen](https://developers.cloudflare.com/fundamentals/account/create-account/).

Danach müssen Sie [einen S3-Bucket auf Cloudflare R2 erstellen – Tab Dashboard](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Merken Sie sich den Namen des Buckets.

Außerdem müssen Sie [einen Anwendungstoken erstellen](https://developers.cloudflare.com/r2/api/tokens/). Merken Sie sich den Access Key, den Secret Key und die Endpoint-URLs auf der letzten Seite, wenn Ihr API-Token erstellt wird.

Sobald dies erledigt ist, sollte die Konfiguration in Ihrer .env-Datei wie folgt aussehen:
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS='{"access_key":"<your access key>","secret_key":"<your secret key>","bucket_name":"<your bucket name>","endpoint_url":"https://<your account id>.r2.cloudflarestorage.com"}'
```
Starten Sie dann Cousins Matter neu: `docker compose restart cousins-matter`

#### Andere S3-kompatible Speicher

Die Konfiguration für andere S3-kompatible Speicher (einschließlich AWS S3, dem ursprünglichen) sollte der von R2 ähneln, wurde aber noch nicht getestet.
Da alle diese Backends dieselbe Implementierung verwenden, müssen Sie Ihr eigenes Image nicht so erstellen, wie es für [nicht getestete Speicher](#non-tested-storages) unten beschrieben ist.
Werfen Sie einen Blick in die [django-storages-Dokumentation](https://django-storages.readthedocs.io/en/latest/index.html), um zu sehen, welche speziellen Variablen für Ihren konkreten Fall in den Optionen gesetzt werden müssen.

### Dropbox

Sie benötigen ein Dropbox-Konto, um diesen Speicher zu verwenden (siehe https://www.dropbox.com/register).
Danach müssen Sie [eine Anwendung erstellen](https://www.dropbox.com/developers/apps). Das Einstellungsformular sollte so aussehen:
![Dropbox-App erstellen](assets/create_dropbox_app.webp). Merken Sie sich den App Key und das App Secret.
Gehen Sie zum Tab „Permissions“ und füllen Sie das Formular wie folgt aus:
![Dropbox-App-Berechtigungen](assets/dropbox_app_permissions.webp)
Vergessen Sie nicht, am Ende auf „Submit“ zu klicken...

Dann holen Sie sich, wie auf der [Django-storages-Dropbox-Seite](https://django-storages.readthedocs.io/en/latest/backends/dropbox.html) beschrieben, Ihren Autorisierungscode und erhalten Sie mit diesem Code den access_token (beginnend mit „sl.“) und den Refresh-Token.

Sobald dies erledigt ist, sollte die Konfiguration in Ihrer .env-Datei wie folgt aussehen:

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS='{"app_key":"<your app key>","app_secret":"<your app secret>","root_path":"/","oauth2_access_token":"<your access token>","oauth2_refresh_token":"<your refresh token>"}'
```

## Nicht getestete Speicher

### Installation des benötigten Python-Pakets

**Hinweis:** Dies ist für alle S3-kompatiblen Backends nicht erforderlich, siehe oben [Andere S3-kompatible Speicher](#other-s3-compatible-storages)

Zuerst müssen Sie ein bestimmtes Python-Paket installieren, das die Anbindung an Ihr Backend implementiert.

Sehen Sie auf der zu Ihrem Backend gehörenden Seite in der [django-storages-Dokumentation](https://django-storages.readthedocs.io/en/latest/index.html) nach, wie Ihr Paket heißt; es sollte in der Form `pip install django-storages[<backend name>]` erscheinen. Merken Sie sich den Wert von `<backend name>`, den Sie unten einsetzen werden.

Es gibt zwei Möglichkeiten, dieses Paket zu installieren; wählen Sie die Methode, die Ihnen am besten passt...

* Entweder erstellen Sie Ihr eigenes Image von Cousins Matter, das vom offiziellen abgeleitet ist, wie folgt:
	1. Erstellen Sie ein Dockerfile wie folgt:

		```
		FROM ghcr.io/leolivier/cousins-matter:latest
		RUN pip install django-storages[<backend name>]
		```

	1. Bauen Sie das neue Image (ändern Sie den Image-Tag nach Belieben):

		```
		docker build -t cousins-matter:local .
		```

	1. Setzen Sie COUSINS_MATTER_IMAGE in Ihrer .env-Datei, um auf `cousins-matter:local` (oder Ihren Tag, falls Sie ihn geändert haben) zu verweisen
	1. Erstellen Sie die Container neu

		```
		docker compose up -d --force-recreate cousins-matter qcluster
		```

	Sie müssen das Image neu bauen und die Container neu erstellen, jedes Mal, wenn eine neue Version ausgeliefert wird.

* Oder Sie aktualisieren die laufenden Container wie folgt:

	```
	docker exec -it cousins-matter pip install django-storages[<backend name>]
	docker exec -it cousins-matter.qcluster pip install django-storages[<backend name>]
	```

	Sie müssen diese 2 Befehle jedes Mal ausführen, wenn Ihre Container mit einem neuen offiziellen Image aktualisiert werden.

__WARNUNG__: In manchen Fällen müssen mehr als ein Paket installiert werden. Wenn Sie beispielsweise Azure Storage mit Managed Identity verwenden, müssen Sie ein weiteres Paket für Managed Identity installieren. Gehen Sie wie oben beschrieben vor und hängen Sie einfach die Namen der anderen Pakete am Ende der `pip install`-Befehlszeile an

### Erstellen der Konfiguration

Werfen Sie einen Blick auf die obigen Konfigurationen für [Dropbox](#dropbox) und [Cloudflare R2](#cloudflare-r2), um zu verstehen, wie die 2 Variablen MEDIA_STORAGE und MEDIA_STORAGE_OPTIONS funktionieren, und sehen Sie in der [django-storages-Dokumentation](https://django-storages.readthedocs.io/en/latest/index.html) für Ihr Backend nach, um diese Konfigurationen an Ihren Fall anzupassen.

MEDIA_STORAGE muss der Seite Ihres Backends entnommen werden. Verwenden Sie den Wert von BACKEND im STORAGES-Block (z. B. storages.backends.azure_storage.AzureStorage für das Azure-Storage-Backend).

MEDIA_STORAGE_OPTIONS muss in einer einzigen Zeile bleiben. Es hat das folgende Format (die Reihenfolge von Anführungszeichen und doppelten Anführungszeichen ist wichtig!)

```
MEDIA_STORAGE_OPTIONS='{"option1":"value1","option2":"value2",...}'
```

Ersetzen Sie option1, option2 durch die in der Dokumentation beschriebenen Variablen in Kleinschreibung und ihre Werte für Ihren Fall.

## Migration vom Medienverzeichnis zu einem externen Speicher

__TIPP__: Wenn Sie bereits viele Dateien in Ihrem Medienverzeichnis gespeichert haben, ist [rclone](https://rclone.org/install/) ein echter Zeitgewinn, um Ihre Dateien auf Ihr neues Backend zu migrieren. Erstellen Sie zuerst eine Konfiguration für Ihr Backend (`rclone config`) und kopieren Sie dann Ihre Mediendateien: `rclone copy ./media <your backend>:<your root>`
