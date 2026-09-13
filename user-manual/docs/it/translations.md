# Traduzioni

## Traduzioni disponibili

Cousins Matter è fornito con le traduzioni in inglese, francese, spagnolo, italiano e tedesco.

La lingua può essere cambiata dinamicamente nel menu a forma di rotella dentata.

**ATTENZIONE**: le traduzioni sono state prodotte in gran parte con l'IA, quindi occasionalmente possono essere imprecise. Se trovi degli errori, apri una issue su GitHub.


## Tradurre in una nuova lingua

Il sito web di Cousins Matter può essere tradotto facilmente in qualsiasi lingua latina LTR seguendo i passi indicati qui sotto. Non è stato testato per le lingue RTL o non latine.

* Clona il repository di Cousins Matter:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

* Genera i file di traduzione:

	```
	python manage.py makemessages -l <language_code>
	```

* Modifica i file django.po nella cartella locale di ogni app.

	Per trovarli, usa il comando seguente:

	```
	ls */locale/<language_code>/LC_MESSAGES/*.po
	```

* Compila le traduzioni:

	```
	python manage.py compilemessages
	```

* Costruisci l'immagine docker:

	```
	docker build -t cousins-matter:<your tag> .
	```

	Non dimenticare di impostare COUSINS_MATTER_IMAGE con il tuo tag nel file .env prima di riavviare il container.

* Apri per favore una issue su GitHub per aggiungere la tua traduzione al repository. Grazie!
