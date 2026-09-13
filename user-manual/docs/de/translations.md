# Übersetzungen

## Verfügbare Übersetzungen

Cousins Matter wird mit englischen, französischen, spanischen, italienischen, deutschen und italienischen Übersetzungen geliefert.

Die Sprache kann dynamisch über das Zahnrad-Menü geändert werden.

**WARNUNG**: Da diese Übersetzungen größtenteils mit KI erstellt wurden, können sie gelegentlich ungenau sein. Wenn Sie Fehler finden, eröffnen Sie bitte ein Issue auf GitHub.


## In eine neue Sprache übersetzen

Die Cousins-Matter-Website kann leicht in jede lateinische LTR-Sprache übersetzt werden, indem Sie die folgenden Schritte befolgen. Nicht getestet für RTL- oder nicht lateinische Sprachen.

* Klonen Sie das Cousins-Matter-Repository:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

* Erzeugen Sie die Übersetzungsdateien:

	```
	python manage.py makemessages -l <language_code>
	```

* Bearbeiten Sie die django.po-Dateien im Ordner „locale“ jeder App.

	Um sie zu finden, verwenden Sie den folgenden Befehl:

	```
	ls */locale/<language_code>/LC_MESSAGES/*.po
	```

* Kompilieren Sie die Übersetzungen:

	```
	python manage.py compilemessages
	```

* Bauen Sie das Docker-Image:

	```
	docker build -t cousins-matter:<your tag> .
	```

	Vergessen Sie nicht, vor dem Neustart des Containers COUSINS_MATTER_IMAGE in der .env-Datei auf Ihren Tag zu setzen.

* Bitte eröffnen Sie ein Issue auf GitHub, um Ihre Übersetzung zum Repository hinzuzufügen. Vielen Dank!
