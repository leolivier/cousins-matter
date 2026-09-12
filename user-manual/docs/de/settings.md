# Einstellungen

## Einführung

Die Einstellungen von Cousins Matter können über eine `.env`-Datei im Hauptverzeichnis der Anwendung verwaltet werden.

Wenn Sie das Skript manage_cousins_matter.py zur Installation von Cousins Matter verwendet haben, wie in [Installation](installation.md) beschrieben, wurde automatisch eine Beispiel-.env-Datei für Sie heruntergeladen und der SECRET_KEY sowie das POSTGRES_PASSWORD wurden automatisch generiert (**überschreiben Sie sie nicht!**).

Wenn Sie mit dem Quellcode arbeiten, kopieren Sie die Datei `.env.example` nach `.env`

In beiden Fällen müssen Sie nun `.env` bearbeiten, um die Eigenschaften entsprechend Ihrem Kontext festzulegen, wie unten beschrieben.

Es stehen viele Einstellungen zur Verfügung, um den technischen Teil Ihrer Website anzupassen...

Vergessen Sie außerdem nicht, einen Blick auf [Anpassung](customizing.md) zu werfen, um das Aussehen und Verhalten Ihrer Website anzupassen.

**WARNUNG**: Läuft der Container bereits, werden Änderungen an den Einstellungen in .env erst nach einem Neustart berücksichtigt.
Führen Sie dazu einfach den folgenden Befehl aus (im Verzeichnis der Website):
```
docker compose restart
```

## Sicherheit

* `SECRET_KEY`: Ein geheimer Schlüssel, der Ihre Website schützt. Er muss extrem komplex sein und geheim gehalten werden! Am einfachsten generieren Sie ihn, indem Sie `python manage_cousins_matter.py rotate-secrets` ausführen. Dieses Skript aktualisiert auch PREVIOUS_SECRET_KEYS in der .env-Datei. Diese Variable wird verwendet, um die Tokens zu entschlüsseln, die mit dem vorherigen Secret Key an Mitglieder gesendet wurden.

	_(Auch hier gilt: Wenn Sie manage_cousins_matter.py zur Installation von Cousins Matter verwendet haben, wurde dies bereits für Sie generiert; überschreiben Sie es nicht)_
* `MAX_REGISTRATION_AGE`: Maximale Gültigkeit in Sekunden für Einladungs-Tokens, Standard ist 2 Tage (2*24*3600)

## Superuser

Bevor Sie `docker compose up -d` zum ersten Mal ausführen, geben Sie die Informationen zum Anlegen des Superusers (d. h. des Administratorkontos) an.

* `ADMIN`: der Kontoname des Superusers
* `ADMIN_PASSWORD`: das Passwort des Superusers
* `ADMIN_EMAIL`: die E-Mail-Adresse des Superusers
* `ADMIN_FIRSTNAME`: der Vorname des Superusers
* `ADMIN_LASTNAME`: der Nachname des Superusers

**ALL DIESE VARIABLEN SIND ZUM ANLEGEN DES SUPERUSER-KONTOS ERFORDERLICH UND HABEN KEINE STANDARDWERTE**

## Verwaltung der Funktionen

Sie können die Funktionen, die den Mitgliedern angeboten werden, in der .env-Datei verwalten.

Ändern Sie dazu die Variable FEATURES_FLAGS auf Grundlage des Inhalts der .env.example-Datei und setzen Sie den Wert jeder auszuschaltenden Funktion auf false.

Der Standardwert von FEATURES_FLAGS ist:
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True;show_public_chats=True;show_private_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_site_stats=True;show_export_members=True;show_change_language=True;show_genealogy=True"
```

**Verfügbare Feature-Flags:**

* `show_birthdays_in_homepage`: Zeigt anstehende Geburtstage auf der Startseite für angemeldete Mitglieder an
* `show_galleries`: Aktiviert die Funktion für Foto- und Videogalerien
* `show_forums`: Aktiviert Forumdiskussionen
* `show_public_chats`: Aktiviert öffentliche Chaträume
* `show_private_chats`: Aktiviert private Chaträume
* `show_classified_ads`: Aktiviert die Funktion für Kleinanzeigen
* `show_polls`: Aktiviert die Funktion für Umfragen
* `show_event_planners`: Aktiviert Umfragen zur Veranstaltungsplanung (Datumsauswahl-Umfragen)
* `show_pages`: Aktiviert die CMS-Seiten-Funktion
* `show_treasures`: Aktiviert die Funktion „Schätze“ (Familienschätze)
* `show_site_stats`: Zeigt die Seite mit den Website-Statistiken an
* `show_export_members`: Ermöglicht den Export des Mitgliederverzeichnisses als PDF
* `show_change_language`: Ermöglicht den Sprachwechsel in der Benutzeroberfläche
* `show_genealogy`: Aktiviert die Genealogie-Funktionen (Stammbäume, GEDCOM-Import/Export)

**WARNUNGEN:**

1. Die Variable INCLUDE_BIRTHDAYS_IN_HOMEPAGE wurde durch das Feature-Flag show_birthdays_in_homepage ersetzt, wie oben gezeigt.
2. FEATURES_FLAGS muss in der .env-Datei in einer einzigen Zeile stehen. Alle Flags werden durch Semikolons getrennt. Wenn Sie diese Variable in Ihrer .env-Datei setzen und ein Flag nicht in der Liste enthalten ist, gilt es als false.

## Allgemeine Anpassung

### Website

* `SITE_NAME`: Der Name der Website, Standard ist 'Cousins Matter!'.
* `SITE_DOMAIN`: Die Domain der Website, z. B. myfamily.com, kein Standardwert.
* `SITE_FOOTER`: Die optionale Fußzeile der Website, z. B. "The Simpsons Family Social Network".
* `SITE_LOGO`: Die optionale relative URL Ihres Website-Logos (oben links). Sie muss ein Verhältnis von 4:1 haben. **Muss im Ordner media/public Ihrer Website gespeichert sein**, sodass **die URL mit '/media/public' beginnen muss** (z. B. SITE_LOGO='/media/public/my-own-logo.jpg')
* `SITE_COPYRIGHT`: Das Copyright Ihrer Website, z. B. 'Copyright © 2024 Cousins Matter'.
* `DARK_MODE`: Aktiviert das dunkle Farbschema. Standard ist False.

### Mitglieder

* `ALLOW_MEMBERS_TO_CREATE_MEMBERS`: Standard ist True. Um zu verhindern, dass Mitglieder andere Mitglieder anlegen und verwalten, setzen Sie False; dann können nur Administratoren dies tun.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS`: Standard ist True. Um zu verhindern, dass Mitglieder andere Mitglieder auf die Website einladen, setzen Sie False; dann können nur Administratoren dies tun.
* `BIRTHDAY_DAYS`: Anzahl der Tage in der Zukunft, für die Geburtstage angezeigt werden, Standard ist 50
* ~~`INCLUDE_BIRTHDAYS_IN_HOMEPAGE`~~: **VERALTET** - Verwenden Sie stattdessen `show_birthdays_in_homepage` in `FEATURES_FLAGS`
* `PDF_SIZE`: PDF-Seitengröße für das gedruckte Verzeichnis. Größe 'A4' oder 'letter'. Standard ist A4.
* `MAX_CSV_FILE_SIZE`(*): Maximale Größe der CSV-Datei für den Mitgliederimport, Standard ist 2MB.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP`: Tragen Sie hier die externe IP Ihres Servers ein. Sie wird für die Anmeldeverfolgung verwendet, wenn die Anmeldung aus dem internen Netzwerk kommt. Standard ist "8.8.8.8".
* `LOGIN_HISTORY_PURGE_DAYS`: Anzahl der Tage, wie lange die Anmeldehistorie aufbewahrt wird (für Administratoren in der Django-Administration sichtbar), Standard ist 365.

### Galerien

* `DEFAULT_GALLERY_PAGE_SIZE`: Anzahl der Fotos pro Galerieseite (auf dem Bildschirm änderbar), Standard ist 25
* `MAX_PHOTO_FILE_SIZE`(*): Maximale Größe jedes Fotos, Standard ist 5MB
* `MAX_VIDEO_FILE_SIZE`(*): Maximale Größe jedes Videos, Standard ist 20MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): Maximale Größe der Zip-Datei für den Sammel-Upload von Galerien, Standard ist 20MB
* `SLIDESHOW_DELAY`: Verzögerung in Sekunden zwischen zwei Fotos einer Diashow, Standard ist 5

### Nachrichten und Chats

* `MESSAGE_MAX_SIZE`(*): Maximale Größe einer Nachricht im Forum oder in den Chats (beachten Sie, dass sie ein Foto enthalten kann), Standard ist 2.5MB.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): Maximale Größe eines Kommentars zu einer Nachricht im Forum oder in den Chats, Standard ist 1000
* `CONTACT_MAX_SIZE`(*): Maximale Größe einer Kontakt-Nachricht, Standard ist 1MB

### Seiten

* `PAGE_MAX_SIZE`(*): Maximale Größe einer statischen Seite, Standard ist 10MB

### Umfragen

* `POLL_MAX_SIZE`(*): Maximale Größe einer Umfrage, Standard ist 1MB

### Kleinanzeigen

* `CLASSIFIED_AD_MAX_SIZE`(*): Maximale Größe einer Kleinanzeige, Standard ist 1MB

### Schätze (Troves)

* `TROVE_FILE_MAX_SIZE`(*): Maximale Größe einer Schatz-Datei, Standard ist 20MB
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): Maximale Größe eines Schatz-Bildes, Standard ist 5MB
* `TROVE_THUMBNAIL_SIZE`(*): Maximale Größe eines Schatz-Vorschaubilds in Pixeln, Standard ist 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): Standardanzahl von Schätzen pro Seite, Standard ist 10

### Kleinanzeigen

* `MAX_PHOTO_PER_AD`: Maximale Anzahl von Fotos pro Kleinanzeige, Standard ist 10

### Genealogie

* `FAMILY_CHART_GENERATIONS`: Anzahl der Generationen, die über und unter der zentralen Person im Familienstammbaum angezeigt werden, Standard ist 4
* `FAMILY_CHART_ROOT_PERSON_ID`: Standard-Personen-ID der Wurzel, die im Familienstammbaum angezeigt wird, wenn keine angegeben ist; Standard ist die ID der ersten Person in der Datenbank
* `GEDCOM_FILE`: GEDCOM-Datei, die für den Genealogie-Export verwendet wird, Standard ist 'genealogy.ged'

## OAuth/SSO-Authentifizierung

* `OAUTH_PROVIDERS`: Durch Kommas getrennte Liste der zu aktivierenden OAuth-Anbieter. Verfügbare Anbieter: `google`, `facebook`, `apple`, `github`, `pocketid` oder jeder `openid_connect`-Anbieter. Standard ist leer (kein OAuth aktiviert).
* `SOCIALACCOUNT_AUTO_SIGNUP`: Ob bei der Anmeldung über einen OAuth-Anbieter eine Bestätigung erforderlich ist. Standard ist False (Bestätigung erforderlich).

Für jeden Anbieter müssen Sie setzen:
* `<PROVIDER>_OAUTH_CLIENT_ID`: OAuth-Client-ID für den Anbieter
* `<PROVIDER>_OAUTH_CLIENT_SECRET`: OAuth-Client-Secret für den Anbieter

Für OpenID-Connect-Anbieter (einschließlich PocketID):
* `<PROVIDER>_SERVER_URL`: URL des OpenID-Connect-Servers

**Beispielkonfiguration:**
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

Siehe [OAuth-Authentifizierung](oauth-authentication.md) für detaillierte Konfigurationsanleitungen für jeden Anbieter.

## Log-Level

* `DJANGO_LOG_LEVEL`: Log-Level für Django und interne Bibliotheken, Standard ist INFO
* `CM_LOG_LEVEL`: Log-Level für Cousins Matter, Standard ist INFO

## Netzwerkkonfiguration

* `ALLOWED_HOSTS`: Durch Kommas getrennte Liste der Hosts. Standard ist '127.0.0.1,localhost,<SITE_DOMAIN\>'. __Sie MÜSSEN ALLOWED_HOSTS für die Produktivumgebung setzen__, und es __MUSS__ Ihre vollständige Website-URL enthalten und manchmal, abhängig von den Netzwerkeinstellungen Ihres Hosts, die allgemeine IP der Website, z. B.:

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: Durch Kommas getrennte Liste der Hosts. Standard ist leer. 

	__WARNUNG!__ Wenn Ihr Protokoll Fehler wie den folgenden zeigt

	`Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

	sollten Sie `CORS_ALLOWED_ORIGINS=<your full domain>` (z. B. https://my.cousins-matter.com) in der `.env`-Datei setzen, 

	__Verwenden Sie nicht die im Fehler gezeigte Python-Syntax!__. 

	Wenn Sie mehrere Hosts haben, listen Sie diese durch Kommas getrennt auf, z. B.

	`CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

	Zur Information: `CSRF_TRUSTED_ORIGINS` wird auf den Wert von `CORS_ALLOWED_ORIGINS` gesetzt

## Internationalisierung

* `LANGUAGE_CODE`: Z. B. 'de' oder 'de-AT'. Standard ist 'en-US'.
* `TIME_ZONE`: Zeitzone, Standard ist 'Europe/Paris'.

## E-Mail-Eigenschaften

* `EMAIL_HOST`: Name des SMTP-Hosts, kein Standardwert
* `EMAIL_PORT`: Port, der am SMTP-Server erreicht werden soll
* `EMAIL_USE_TLS`: Der SMTP-Server verwendet STARTTLS, wenn true, Standard ist true
* `EMAIL_USE_SSL`: Der SMTP-Server verwendet SSL, wenn true, Standard ist false
* `EMAIL_HOST_USER`: Benutzername für die Verbindung zum SMTP-Server.
* `EMAIL_HOST_PASSWORD`: Passwort für die Verbindung zum SMTP-Server
* `DEFAULT_FROM_EMAIL`: Standard-E-Mail-Adresse zum Versenden von E-Mails

## Datenbank

* `POSTGRES_USER`: Der PostgreSQL-Benutzer, Standard ist 'cousinsmatter'
* `POSTGRES_PASSWORD`: Das PostgreSQL-Passwort. Es wird automatisch generiert, wenn Sie manage_cousins_matter.py zum Installieren oder Migrieren von Cousins Matter verwenden. __WARNUNG!__ Verwenden Sie als Sonderzeichen nur -_./*, wenn Sie es ändern möchten. Vermeiden Sie unbedingt : und @ !
* `POSTGRES_DB`: Die PostgreSQL-Datenbank, Standard ist 'cousinsmatter'
* `POSTGRES_HOST`: Der PostgreSQL-Host, Standard ist 'postgres'

* `REDIS_HOST`: Der Redis-Host, Standard ist 'redis'

## Anderer Medienspeicher

* `MEDIA_STORAGE` und `MEDIA_STORAGE_OPTIONS`: Siehe [Medienspeicher](/media-storage.md)

## HINWEISE

__(*) WARNUNG:__ Wenn Sie eine der Variablen ändern möchten, die die Größe der hochladbaren Inhalte steuern, und Sie den Nginx-Reverse-Proxy verwenden, prüfen Sie bitte den Wert von `client_max_body_size` in config/nginx/nginx.conf, damit er größer bleibt als die oben geänderten Größenvariablen. Andernfalls erhalten Sie einen 413-Fehler von Nginx. Der vorgegebene Standardwert ist hoch (20MB), aber Sie müssen ihn möglicherweise erhöhen, um größere Videos zu unterstützen.
