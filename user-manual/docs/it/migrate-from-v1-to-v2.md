# Migrare dalla Versione 1 alla Versione 2

## Introduzione

La versione 2 di Cousins Matter è una grande riscrittura della versione 1 e non è direttamente compatibile con la versione 1.
Tra i grandi cambiamenti:

* il database è stato migrato da sqlite3 a postgresql per garantire prestazioni e scalabilità migliori.
* cousins matter è ora composto da almeno 4 container docker:

	* il server web
	* il database
	* redis
	* il server dei task asincroni

	e richiederà quindi docker compose per funzionare.

## Prerequisiti

Devi avere Cousins Matter v1 installato e funzionante sul tuo sistema.

Ti servirà anche un ambiente Python 3.14+ per eseguire lo script di migrazione.

## Procedura

1. Ferma Cousins Matter v1

	```
	cd <cousins-matter-v1-directory>
	docker compose down
	```

1. Scarica lo script di amministrazione di Cousins Matter

	Sostituisci nel link qui sotto il segnaposto <release\> con la release corrente di Cousins Matter:
![GitHub Release](https://img.shields.io/github/v release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
	mkdir scripts
	curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
	```

1. Esegui lo script di migrazione

	```
	python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <release>]
	```

	Se la release non viene fornita, la migrazione avverrà verso l'ultima release della serie v2.X (consigliato).

	**Fai attenzione al log dello script di migrazione!** Ti mostrerà l'avanzamento della migrazione e gli eventuali problemi o azioni da compiere.

1. Aggiorna le tue impostazioni

	Le impostazioni di Cousins Matter v2 sono diverse da quelle della v1. Aggiorna il tuo file .env per allinearlo alle impostazioni di Cousins Matter v2.

	Le impostazioni di Cousins Matter v2 sono descritte in dettaglio nella pagina [Impostazioni](settings.md).
	In particolare, la migrazione aggiorna il file .env.example per allinearlo alle impostazioni di Cousins Matter v2. Confronta quindi questo nuovo file .env.example con il tuo file .env e aggiorna di conseguenza il tuo file .env.

	Fai attenzione anche al fatto che alcuni valori predefiniti sono cambiati. Per esempio:

	* ALLOW_MEMBERS_TO_CREATE_MEMBERS e ALLOW_MEMBERS_TO_INVITE_MEMBERS ora valgono True per impostazione predefinita
	* ALLOWED_HOSTS ora contiene il valore di SITE_DOMAIN ('127.0.0.1,localhost,$SITE_DOMAIN') per impostazione predefinita
	* DARK_MODE ora vale False per impostazione predefinita
	* SESSION_COOKIE_DOMAIN ora è impostato su .$SITE_DOMAIN per impostazione predefinita
	* SITE_PORT ora vale 0 se SITE_DOMAIN è impostato, 8000 altrimenti

	Inoltre, nuove variabili sono state aggiunte al file .env ma hanno valori predefiniti ragionevoli.

	* POSTGRES_USER=cousinsmatter
	* POSTGRES_DB=cousinsmatter
	* POSTGRES_HOST=postgres
	* POSTGRES_PASSWORD viene calcolata automaticamente al momento della migrazione
	* PREVIOUS_SECRET_KEYS viene calcolata automaticamente al momento della migrazione (e la SECRET_KEY viene ruotata)

1. Avvia Cousins Matter v2

	```
	docker compose pull  # scarica tutte le immagini
	docker compose up -d
	```
