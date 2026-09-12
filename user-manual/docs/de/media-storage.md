# Medienspeicher

## WARNUNGEN 

* __Dies ist derzeit eine <span class="blinking-text"><u>BETA</u></span>-Funktion!__
* __Diese Einstellungen sind komplexer und <u>fortgeschrittenen Benutzern vorbehalten</u>.__

## Standard-Medienspeicher

Standardmäßig werden die Medien im Unterverzeichnis 'media' im selben Dateisystem wie Cousins Matter gespeichert.

Dies ist sehr einfach, hat aber einige Nachteile, insbesondere im Bereich der Sicherheit, wie in [diesem Artikel](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html) erklärt wird.

## Andere Medienspeicher

Cousins Matter unterstützt auch S3-Medienspeicher mithilfe des Pakets 'django-storages'. Um einen solchen Speicher einzurichten, müssen Sie nur zwei neue Variablen in Ihrer .env-Datei definieren: MEDIA_STORAGE und MEDIA_STORAGE_OPTIONS.

**Bisher wurde nur der Cloudflare-R2-Speicher getestet und erprobt**, aber andere S3-Speicher sollten funktionieren, solange Sie die richtige Konfiguration finden. Siehe [Andere S3-kompatible Speicher](#other-s3-compatible-storages) unten.

Wenn Sie eine funktionierende Konfiguration für einen nicht getesteten Speicher erstellen, erstellen Sie bitte einen Pull Request auf GitHub auf dieser Seite, um zu erklären, wie es funktioniert.

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

Werfen Sie einen Blick in die [django-storages-Dokumentation](https://django-storages.readthedocs.io/en/latest/index.html), um zu sehen, welche speziellen Variablen für Ihren konkreten Fall in den Optionen gesetzt werden müssen.


## Migration vom Medienverzeichnis zu einem externen S3-Speicher

Dazu können Sie die S3-Storage-Werkzeuge verwenden. Bei AWS S3 können Sie zum Beispiel

```
$ aws s3 sync ./media s3://YOUR_BUCKET/media/
```

__TIPP__: Unabhängig von Ihrem S3-Anbieter ist [rclone](https://rclone.org/install/) ein echter Zeitgewinn, um Ihre Dateien auf Ihr neues Backend zu migrieren. Erstellen Sie zuerst eine Konfiguration für Ihr Backend (`rclone config`) und kopieren Sie dann Ihre Mediendateien: `rclone copy ./media <your backend>:<your root>`
