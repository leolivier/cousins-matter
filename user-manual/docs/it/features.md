## Funzionalità

### Gestione dei membri

* I membri possono essere elencati, filtrati per nome e cognome e ordinati

	![members](assets/members.webp)

* L'amministratore del sito o qualsiasi membro (a seconda delle impostazioni) può invitare altri membri tramite email

	![invite](assets/invite.webp)

* Chiunque può richiedere un invito: la richiesta verrà inviata via email all'amministratore del sito, che potrà così invitarlo. Le richieste di invito sono protette da un captcha.

	![request-invite](assets/request-invite.webp)

* I membri possono creare membri "gestiti", ovvero membri che non sono attivi sul sito (ad esempio bambini piccoli o persone anziane)
* I membri gestiti possono essere attivati dai membri che li gestiscono (ad esempio quando un bambino è abbastanza grande per essere attivo sul sito).
* I membri possono essere importati in blocco tramite file CSV
* I membri possono aggiornare il proprio profilo e quello dei membri che gestiscono
* I membri possono essere contrassegnati come deceduti con la data di morte (utile per la genealogia e la storia familiare)

	![profile](assets/profile.webp)

* L'elenco dei membri può essere stampato in formato PDF

	![directory](assets/directory.webp)

* Possono essere visualizzati i compleanni dei prossimi 50 giorni (50 è modificabile nelle impostazioni)

	![birthdays](assets/birthdays.webp)

### Autenticazione

* Autenticazione standard con email/password
* Autenticazione OAuth/SSO con più provider:
	* Google
	* Facebook
	* Apple
	* GitHub
	* PocketID (OpenID Connect self-hosted)
	* Qualsiasi provider compatibile con OpenID Connect
* Vedi [Autenticazione OAuth](oauth-authentication.md) per la configurazione dettagliata

### Sicurezza e cronologia degli accessi

* Tutti i tentativi di accesso vengono tracciati automaticamente con la geolocalizzazione dell'IP
* La cronologia degli accessi viene conservata per audit di sicurezza (visibile agli amministratori del sito nell'admin di Django)
* Eliminazione automatica dei vecchi record di accesso dopo un periodo di conservazione configurabile
* Aiuta gli amministratori a individuare tentativi di accesso non autorizzati

### Follower e notifiche

* I membri possono seguire altri membri per essere avvisati delle loro attività
* I membri possono seguire stanze di chat, forum, gallerie e altri contenuti
* Notifiche email automatiche quando un contenuto seguito viene aggiornato
* Frequenza di notifica configurabile per ogni membro:
	* **Immediata** - ricevi le notifiche non appena si verificano gli eventi
	* **Oraria** - ricevi un riepilogo degli eventi ogni ora
	* **Giornaliera** - ricevi un digest giornaliero degli eventi
	* **Settimanale** - ricevi un riepilogo settimanale
	* **Mensile** - ricevi un riepilogo mensile
	* **Mai** - disattiva completamente le notifiche
* Ogni membro può configurare la frequenza di notifica preferita nelle impostazioni del proprio profilo
* Il raggruppamento delle notifiche riduce il sovraccarico di email tenendo comunque i membri informati

### Gallerie

* Tutti i membri attivi possono creare gallerie e aggiungervi foto e video
* Le gallerie possono contenere sottogallerie a qualsiasi profondità
* Foto e video possono essere importati in blocco usando file zip. Ogni cartella del file zip diventa una galleria. Gli aggiornamenti sono gestiti
* La visualizzazione delle foto delle gallerie è paginata
* Foto e video possono essere mostrati a schermo intero e in modalità presentazione (slideshow) con un intervallo configurabile

### Forum

* I membri attivi possono creare post
* I membri attivi possono rispondere ai post di altri membri o aggiungere semplici commenti

### Chat

* I membri collegati possono chattare in diretta con gli altri membri collegati
* Cousins Matter gestisce tutte le stanze di chat di cui hai bisogno
* I membri possono creare stanze di chat private e scegliere i membri che possono parteciparvi.
	Il creatore della stanza ne diventa admin e può aggiungere altri membri ed eleggere admin tra questi membri.
	Gli admin possono invitare altri membri e altri admin

### Pagine / CMS

Funzionalità CMS di base: gli admin possono creare pagine HTML statiche e pubblicarle sul sito.
Anche la home page può essere configurata in questo modo, così come l'informativa sulla privacy, le pagine "informazioni"...
Le pagine pubbliche (quelle mostrate nel menu Pagine anche se non hai effettuato l'accesso) possono essere create e pubblicate da qualsiasi membro admin. Il loro URL deve iniziare con '/publish/'
Le pagine private (quelle mostrate nel menu Pagine solo se hai effettuato l'accesso) possono essere create e pubblicate da qualsiasi membro admin. Il loro URL deve iniziare con '/private/'
I messaggi degli admin sono un tipo particolare di pagina mostrata a tutti i membri collegati in cima al sito. Il loro URL deve iniziare con '/admin-message/'
Altre pagine specifiche predefinite possono essere modificate da qualsiasi membro admin. Si raggiungono dal menu admin alla voce "Edit pages" e mostrano rispettivamente la home page quando non sei connesso (/home/unauthenticated/\<lang>), quando sei connesso (/home/authenticated/\<lang>) e l'informativa sulla privacy (/about/privacy-policy/\<lang>).

### Tesori (Troves)

È un luogo in cui puoi mettere in risalto i tesori familiari digitali, che si tratti di testi, musica o video

### Sondaggi

Qualsiasi membro attivo può creare un sondaggio e qualsiasi membro attivo può rispondere a un sondaggio attivo.
I sondaggi hanno una data di pubblicazione e una data di chiusura. Possono contenere più domande e le domande possono essere

* semplici domande sì/no: spunta la casella di controllo
* testo libero: inserisci il testo formattato che vuoi
* data: scegli una data
* scelte multiple: scegli un'opzione in un elenco

### Pianificazione degli eventi

In qualità di sottomodulo del modulo dei sondaggi, qualsiasi membro attivo può creare un'indagine di pianificazione di un evento per definire quando questo dovrebbe svolgersi. Questo aggiunge al modulo dei sondaggi i seguenti tipi di scelte:

* scegliere una data in un elenco proposto
* scegliere più date in un elenco proposto

### Annunci

Qualsiasi membro attivo può pubblicare un annuncio visibile a tutti gli altri membri. Se un membro è interessato a un annuncio, può inviare un messaggio a chi lo ha pubblicato, che riceverà un'email.

### Genealogia

Qualsiasi membro attivo può aggiungere persone alla genealogia del sito. Puoi aggiungere persone alla genealogia inserendo i loro dati nei moduli oppure importando un file GEDCOM. Puoi esportare la genealogia in formato GEDCOM. La genealogia può essere visualizzata come albero dinamico o come elenchi di persone o famiglie.
