# Migration von Version 1 auf Version 2

## Einführung

Die Version 2 von Cousins Matter ist eine umfassende Neuentwicklung der Version 1 und ist nicht direkt mit der Version 1 kompatibel. 
Zu den großen Änderungen gehören unter anderem:

* die Datenbank wurde von sqlite3 auf PostgreSQL migriert, um bessere Leistung und Skalierbarkeit zu ermöglichen.
* Cousins Matter besteht jetzt aus mindestens 4 Docker-Containern:

	* dem Webserver
	* der Datenbank
	* Redis
	* dem Server für asynchrone Aufgaben

	und benötigt daher docker compose für den Betrieb.

## Voraussetzungen

Cousins Matter v1 muss auf Ihrem System installiert und funktionierend sein.

Sie benötigen außerdem eine Python-3.14+-Umgebung, um das Migrationsskript auszuführen.

## Vorgehensweise

1. Stoppen Sie Cousins Matter v1

	```
	cd <cousins-matter-v1-directory>
	docker compose down
	```

1. Laden Sie das Cousins-Matter-Admin-Skript herunter

	Bitte ersetzen Sie im unten stehenden Link den Platzhalter <release\> durch die aktuelle Version von Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
	mkdir scripts
	curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
	```

1. Führen Sie das Migrationsskript aus

	```
	python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <release>]
	```

	Wird keine Version angegeben, wird auf die neueste Version der Reihe v2.X migriert (empfohlen).

	**Achten Sie auf das Protokoll des Migrationsskripts!** Es zeigt Ihnen den Fortschritt der Migration sowie mögliche Probleme oder durchzuführende Aktionen an.

1. Aktualisieren Sie Ihre Einstellungen

	Die Einstellungen von Cousins Matter v2 unterscheiden sich von denen der v1. Bitte passen Sie Ihre .env-Datei an die Einstellungen von Cousins Matter v2 an.

	Die Einstellungen von Cousins Matter v2 sind auf der Seite [Einstellungen](settings.md) im Detail beschrieben.
	Insbesondere aktualisiert die Migration die Datei .env.example, um sie an die Einstellungen von Cousins Matter v2 anzupassen. Vergleichen Sie daher bitte diese neue Datei .env.example mit Ihrer .env-Datei und aktualisieren Sie Ihre .env-Datei entsprechend. 
	
	Achten Sie außerdem darauf, dass sich einige Standardwerte geändert haben. Zum Beispiel:

	* ALLOW_MEMBERS_TO_CREATE_MEMBERS und ALLOW_MEMBERS_TO_INVITE_MEMBERS sind jetzt standardmäßig True
	* ALLOWED_HOSTS enthält jetzt standardmäßig den Wert von SITE_DOMAIN ('127.0.0.1,localhost,$SITE_DOMAIN')
	* DARK_MODE ist jetzt standardmäßig False
	* SESSION_COOKIE_DOMAIN ist jetzt standardmäßig auf .$SITE_DOMAIN gesetzt
	* SITE_PORT ist jetzt 0, wenn SITE_DOMAIN gesetzt ist, sonst 8000

	Außerdem wurden der .env-Datei neue Variablen hinzugefügt, die aber vernünftige Standardwerte haben.

	* POSTGRES_USER=cousinsmatter
	* POSTGRES_DB=cousinsmatter
	* POSTGRES_HOST=postgres
	* POSTGRES_PASSWORD wird zum Zeitpunkt der Migration automatisch berechnet
	* PREVIOUS_SECRET_KEYS wird zum Zeitpunkt der Migration automatisch berechnet (und der SECRET_KEY wird rotiert)

1. Starten Sie Cousins Matter v2

	```
	docker compose pull  # get all the images
	docker compose up -d
	```
