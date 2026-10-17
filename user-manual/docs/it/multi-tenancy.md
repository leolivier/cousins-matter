# Multi-tenancy (più famiglie su un'unica installazione)

Cousins Matter può servire **più famiglie (tenant) da un'unica installazione**,
con i dati di ogni famiglia isolati. Questa pagina documenta la funzionalità e
il suo deployment.

## Attivare la funzionalità

La funzionalità è **disattivata per impostazione predefinita**: un'installazione
mono-famiglia si comporta esattamente come l'app classica. Per attivarla, imposta
in `.env`:

```
MULTI_TENANT_ENABLED=True
```

Questo monta gli URL `/tenants/` (iscrizione di una famiglia + gestione) e mostra
il collegamento "Create a new family" nella pagina di login. Se è disattivata,
tutto questo restituisce un 404.

## Concetti

| Concetto | Dove |
|---|---|
| **Famiglia (tenant)** | `tenants.Tenant` — nome, slug, `is_active` |
| **Admin di famiglia** | `Member.role = "admin"` — gestisce i membri e le impostazioni della propria famiglia |
| **Admin della piattaforma** | `is_superuser` — cross-tenant, vive sul tenant `system`, accesso alla Django-admin (`is_staff`) |
| **Isolamento (primario)** | manager ORM con scope per tenant (`TenantManager`) + `TenantMiddleware` |
| **Isolamento (di riserva)** | row-level security di PostgreSQL (vedi sotto) |

Due tenant sono creati dalla migrazione e non possono essere eliminati: `default`
(assegnato quando non se ne può risolvere nessuno) e `system` (casa degli admin
della piattaforma).

## Creare una famiglia

* **Self-service**: con la funzionalità attiva, la pagina di login propone
  *"Create a new family"*. Chi la crea si iscrive con verifica dell'email e
  diventa l'admin della famiglia.
* **Da parte di un admin della piattaforma**: `/tenants/create/` crea la famiglia e può inviare via email
  un invito (link vincolato al tenant) al suo primo admin.

Un identificatore di famiglia (slug) è derivato dal suo nome; gli slug riservati
(`default`, `system`, `admin`, …) vengono rifiutati.

## Accedere a una famiglia

Tutti accedono dalla pagina di login standard — la famiglia viene risolta automaticamente
dall'account connesso; non esiste un URL per famiglia. Un indirizzo email appartiene a
una sola famiglia: per entrare in un'altra famiglia serve un altro indirizzo email.

* **Chi crea la famiglia**: dopo essersi iscritto tramite *"Create a new family"*,
  l'account resta inattivo finché non si fa clic sul link dell'email di verifica;
  poi si accede normalmente e si è l'admin della famiglia.
* **Gli altri membri**: oppure accettare l'invito inviato via email dall'admin della
  famiglia (link vincolato al tenant → iscrizione → verifica dell'email), oppure
  presentare una richiesta di adesione (modulo con captcha) che un admin della famiglia
  deve approvare. In entrambi i casi, accedere poi dalla pagina di login standard.

## Impostazioni della famiglia

Un admin di famiglia modifica le impostazioni della propria famiglia in
**Family settings** (menu a discesa nella barra di navigazione): nome del sito,
logo, copyright, piè di pagina, dark mode, formato pagina PDF, lingua, fuso
orario, finestra sui compleanni, permessi dei membri (creare/invitare) e radice
dell'albero genealogico. I valori uguali ai valori predefiniti globali
**non vengono memorizzati**, quindi una modifica globale si propaga comunque alle
famiglie che non li hanno mai personalizzati. Le email indirizzate a "the admin"
(modulo di contatto, inviti, notifiche di decesso) sono instradate
all'**admin della famiglia**.

## Ciclo di vita

* **Disattivazione** (`/tenants/<slug>/toggle-active/`): i membri della famiglia
  vengono disconnessi e non possono accedere finché la famiglia non viene riattivata.
* **Cancellazione definitiva** (`/tenants/<slug>/delete/`, oppure `manage.py delete_tenant
  <slug>`): rimuove in modo permanente la famiglia e tutti i suoi dati. Rifiuta il
  tenant `system` e ogni famiglia ancora attiva; richiede di digitare lo slug.

## Row-level security di PostgreSQL (irrigidimento opzionale)

Lo scoping ORM è il livello primario di isolamento. Per una difesa in profondità,
puoi far sì che sia il database stesso a rifiutare le scritture cross-tenant. La RLS
è attiva quando `MULTI_TENANT_ENABLED=True` **e** `POSTGRES_RUNTIME_USER` è impostato.

**Con Docker**, imposta in `.env`:

```
MULTI_TENANT_ENABLED=True
POSTGRES_RUNTIME_USER=cm_app
POSTGRES_RUNTIME_PASSWORD=<password robusta>
```

e riavvia i container dell'applicazione:

```
docker compose restart cousins-matter qcluster
```

All'avvio l'entrypoint esegue le migrazioni **come proprietario**
(`POSTGRES_USER`): la migrazione RLS (`tenants.0003_rls`) crea il ruolo runtime con
privilegi di solo DML e applica le policy; quindi il server e qcluster si riavviano e
si connettono con il ruolo runtime. Nulla da eseguire a mano.

**Con un'installazione manuale (senza Docker)**, imposta le stesse variabili ed esegui
`manage.py migrate` **come proprietario** (`POSTGRES_USER`) — è esattamente ciò che
l'entrypoint automatizza qui sopra.

**A cosa serve `POSTGRES_USER`**: è il proprietario (superuser) creato dall'immagine
PostgreSQL. Esegue le migrazioni — crea il ruolo runtime, i suoi privilegi di solo DML
e le policy — e, in quanto proprietario, aggira completamente la RLS; per questo
`FORCE ROW LEVEL SECURITY` non viene mai usato. Il server e qcluster lo usano solo
come ripiego quando `POSTGRES_RUNTIME_USER` non è impostato (la RLS non ha allora effetto).

Comportamento delle policy per il ruolo runtime:

* tutte le tabelle con scope per tenant (galleries, chat, forum, annunci, sondaggi,
  tesori, genealogia, pagine): le righe al di fuori del tenant della sessione sono
  invisibili **e** non scrivibili;
* `members_member`: le letture restano permissive (il login via email avviene prima che
  il tenant sia noto), ma INSERT/UPDATE/DELETE sono rigidamente limitati;
* il middleware imposta `app.current_tenant_id` per ogni richiesta e lo ripristina sempre
  successivamente (le connessioni in pool non fanno mai trapelare un tenant); i superuser
  della piattaforma ottengono `app.bypass` e possono quindi amministrare in modalità cross-tenant;
* le migrazioni girano come proprietario, il che aggira la RLS — è voluto, ed è il
  motivo per cui `FORCE ROW LEVEL SECURITY` non viene mai usato.

## Perimetro attuale

Tutte le app del prodotto hanno scope per tenant e sono coperte dalla row-level security:
`members`, `galleries`, `chat`, `troves`, `forum`, `classified ads`, `polls`, `genealogy` e
`pages` — 22 tabelle, migrazioni da `tenants.0003_rls` a `tenants.0010_rls_pages`.
Solo le tabelle di infrastruttura (sessioni Django, account allauth) restano globali;
lo scoping ORM si applica a tutto il resto.
