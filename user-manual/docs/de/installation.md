# Installation von Cousins Matter

Dies wurde unter Linux und Windows+WSL2 mit Ubuntu bzw. Debian und installiertem Docker Desktop getestet. (Das Installationsskript wurde unter MacOS noch nicht getestet, sollte aber mit nur wenigen Änderungen funktionieren.)

## Installation in der Produktivumgebung

### Voraussetzungen

Falls noch nicht geschehen, installieren Sie Docker auf Ihrem Server:
```
curl https://get.docker.com | sh
```

Sie benötigen außerdem eine Python-3.14+-Umgebung, um das Admin-Skript von Cousins Matter auszuführen.

### Herunterladen und Ausführen des Cousins-Matter-Admin-Skripts

Bitte ersetzen Sie im unten stehenden Link den Platzhalter **<release\>** durch die aktuelle Version von Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <directory>] [-r <release>]
```

* wird die Option -d <directory> nicht angegeben, wird im aktuellen Verzeichnis installiert
* wird die Option -r <release> nicht angegeben, wird die neueste Version installiert

Dieser Befehl wird:

* die für Cousins Matter benötigten Dateien herunterladen;
* die erforderlichen Verzeichnisse anlegen;
* die Basis-.env-Datei aus einem Beispiel erstellen;
* einen Editor auf der .env-Datei öffnen, damit Sie sie an Ihre Bedürfnisse anpassen können (siehe Seite [Einstellungen](settings.md)). __Vergessen Sie insbesondere nicht, die Informationen zum Anlegen des Superusers einzutragen__.

Dieses Skript kann Ihnen auch bei der [Migration von Cousins Matter von v1 auf v2](migrate-from-v1-to-v2.md) und beim [gelegentlichen Rotieren Ihres Secret Keys](other-management-operations.md#ihren-secret-key-rotieren) helfen.

Um die verfügbaren Befehle zu sehen, führen Sie aus:

```
python manage_cousins_matter.py -h
```

Um Hilfe zu einem bestimmten Befehl zu erhalten, führen Sie aus:
```
python manage_cousins_matter.py <command> -h
```

### Cousins Matter starten

```
cd <directory>
docker compose up -d
```

__Beim ersten Mal__ gehen Sie zu http://127.0.0.1:8000/members/profile, melden Sie sich mit dem gerade erstellten Administratorkonto an und vervollständigen Sie Ihr Profil.

**Und fertig sind Sie!**

## Build aus dem Quellcode

* Installieren Sie Docker und uv, falls noch nicht geschehen

	```
	curl https://get.docker.com | sh
  pip install uv
	```

* Klonen Sie das Git-Repository:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

**Hinweis für Beiträger:** Wenn Sie zur Entwicklung von cousins-matter beitragen möchten, forken Sie zuerst das Projekt auf GitHub und klonen Sie Ihr eigenes Repository.

* Erstellen und synchronisieren Sie Ihre Python-Virtual-Environment:
  ```
  uv sync
	```

* Aktualisieren Sie Ihre Einstellungen:
	Kopieren Sie `.env.example` nach `.env` und bearbeiten Sie `.env`, um die Eigenschaften nach Ihren Bedürfnissen festzulegen, siehe Seite [Einstellungen](settings.md).

	Sie können den SECRET_KEY automatisch erstellen, indem Sie den folgenden Befehl ausführen:

	```
	./manage_cousins_matter.sh rotate-secrets
	```

* bauen Sie das Docker-Image:

	```
	make build t=cousins-matter:local
	```

* Verwenden Sie Ihr lokales Image, indem Sie die folgende Zeile zur .env-Datei hinzufügen:
	```
	COUSINS_MATTER_IMAGE=cousins-matter:local
	```

* Starten Sie alles:

	```
	make up
	```

### Betrieb außerhalb von Docker

Wenn Sie Ihre Installation debuggen möchten, können Sie sie außerhalb von Docker betreiben.

Verwenden Sie dazu anstelle von `make up`:
```
make up4run  # startet die benötigten Container: postgres, redis und qcluster (mit dem zuvor gebauten Image)
# um cousins-matter im Entwicklungsmodus zu starten
make run  # lädt nach jeder Codeänderung automatisch neu
# um Tests auszuführen (keine UI-Tests)
make test [t=<test name>]
# um UI-Tests auszuführen
make test-ui [t=<test name>]
# alle weiteren make-Befehle erhalten Sie einfach durch
make
```
oder starten Sie das Debugging aus Ihrer IDE (das Projekt ist für Visual Studio Code bereits in der Datei .vscode/launch.json konfiguriert)
