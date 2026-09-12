# Installazione di Cousins Matter

Il tutto è stato testato su Linux e su Windows+WSL2 con Ubuntu o Debian + Docker Desktop installato. (Lo script di installazione non è ancora stato testato su MacOS, ma dovrebbe funzionare con pochissime modifiche)

## Installazione in produzione

### Prerequisiti

Se non l'hai già fatto, installa Docker sul tuo server:
```
curl https://get.docker.com | sh
```

Ti servirà anche un ambiente Python 3.14+ per eseguire lo script di amministrazione di Cousins Matter.

### Scaricare ed eseguire lo script di amministrazione di Cousins Matter

Sostituisci nel link qui sotto il segnaposto **<release\>** con la release corrente di Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <directory>] [-r <release>]
```

* se la directory -d non viene fornita, l'installazione avviene nella directory corrente
* se la release -r non viene fornita, viene installata l'ultima release

Questo comando:

* scaricherà i file necessari per Cousins Matter;
* creerà le directory necessarie;
* creerà il file .env di base a partire da un esempio;
* aprirà un editor sul file .env per adattarlo alle tue esigenze (vedi la pagina [Impostazioni](settings.md)). In particolare, __non dimenticare di aggiungere le informazioni per creare il superuser__.

Questo script può anche aiutarti a [migrare dalla v1 alla v2 di Cousins Matter](migrate-from-v1-to-v2.md) e a [ruotare la chiave segreta di tanto in tanto](other-management-operations.md#ruotare-la-tua-chiave-segreta).

Per conoscere i diversi comandi disponibili, esegui:

```
python manage_cousins_matter.py -h
```

Per ottenere aiuto su un comando specifico, esegui:

```
python manage_cousins_matter.py <command> -h
```


### Avviare Cousins Matter

```
cd <directory>
docker compose up -d
```

__La prima volta__, vai su http://127.0.0.1:8000/members/profile, accedi con l'account amministratore appena creato e completa il tuo profilo.

**Ed è tutto pronto!**

## Compilare dai sorgenti

* Installa Docker e uv se non ancora fatto

	```
	curl https://get.docker.com | sh
  pip install uv
	```

* Clona il repository git:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

**Nota per i contributori:** se vuoi contribuire allo sviluppo di cousins-matter, prima fai un fork del progetto su github e poi clona il tuo repository.

* Crea e sincronizza il tuo ambiente virtuale python:
  ```
  uv sync
	```

* Aggiorna le impostazioni:
	Copia `.env.example` in `.env` e modifica `.env` per impostare le proprietà in base alle tue esigenze, vedi la pagina [Impostazioni](settings.md).

	Puoi creare automaticamente la SECRET_KEY eseguendo il comando seguente:

	```
	./manage_cousins_matter.sh rotate-secrets
	```

* compila l'immagine docker:

	```
	make build t=cousins-matter:local
	```

* Usa la tua immagine locale aggiungendo la riga seguente al file .env:
	```
	COUSINS_MATTER_IMAGE=cousins-matter:local
	```

* Avvia tutto:

	```
	make up
	```

### Eseguirlo fuori da Docker

Se vuoi fare il debug dell'installazione, puoi eseguirlo fuori da Docker.

Per farlo, invece di avviare `make up`, usa:
```
make up4run  # avvierà i container necessari: postgres, redis e qcluster (usando l'immagine costruita in precedenza)
# per avviare cousins-matter in modalità sviluppo
make run  # ricaricherà automaticamente dopo ogni modifica al codice
# per eseguire i test (senza i test UI)
make test [t=<test name>]
# per eseguire i test UI
make test-ui [t=<test name>]
# per ottenere tutti gli altri comandi make esegui semplicemente
make
```
oppure avvia il debug dal tuo IDE (il progetto è già configurato per Visual Studio Code nel file .vscode/launch.json)
