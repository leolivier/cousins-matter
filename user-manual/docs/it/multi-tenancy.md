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
puoi far sì che sia il database stesso a rifiutare le scritture cross-tenant:

1. Scegli un ruolo non proprietario, ad esempio `cm_app`, con una password robusta.
2. In `.env`, imposta `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (e
   mantieni `MULTI_TENANT_ENABLED=True`).
3. Esegui `manage.py migrate` **come proprietario** (`POSTGRES_USER`) — la migrazione RLS
   (`tenants.0003_rls`) crea il ruolo, concede privilegi di solo DML
   e le policy. L'entrypoint del container lo fa automaticamente:
   l'inizializzazione gira come proprietario, solo il server di lunga durata usa il ruolo
   runtime.

Comportamento delle policy per il ruolo runtime:

* le tabelle con scope per tenant esterne ai modelli delle app stesse (galleries): le righe al di fuori
  del tenant della sessione sono invisibili **e** non scrivibili;
* `members_member`: le letture restano permissive (il login via email avviene prima che
  il tenant sia noto), ma INSERT/UPDATE/DELETE sono rigidamente limitati;
* il middleware imposta `app.current_tenant_id` per ogni richiesta e lo ripristina sempre
  successivamente (le connessioni in pool non fanno mai trapelare un tenant); i superuser
  della piattaforma ottengono `app.bypass` e possono quindi amministrare in modalità cross-tenant;
* le migrazioni girano come proprietario, il che aggira la RLS — è voluto, ed è il
  motivo per cui `FORCE ROW LEVEL SECURITY` non viene mai usato.

## Perimetro attuale

Oggi `members` e `galleries` hanno scope per tenant. Convertire le restanti
app (chat, forum, sondaggi, annunci, pagine, tesori, genealogia) segue
lo stesso schema (classe base `TenantModel` + indici composti); finché non accadrà,
i dati di quelle app sono condivisi tra le famiglie di un'installazione.
