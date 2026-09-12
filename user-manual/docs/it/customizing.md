# Personalizza il tuo sito

## Impostazioni
Vedi [Impostazioni](settings.md) per la personalizzazione tramite modifica delle impostazioni.

### Gestione delle funzionalità
Tramite le impostazioni puoi anche gestire le funzionalità che verranno offerte ai membri, come spiegato in [Gestione delle funzionalità](settings.md/#features-management)

### Preferenze di notifica
I membri possono configurare la frequenza delle notifiche email nelle impostazioni del proprio profilo. Vedi [Funzionalità - Follower e notifiche](features.md#follower-e-notifiche) per i dettagli.

## Creazione di pagine
Gli admin possono creare o aggiornare pagine statiche usando la funzione "Edit Page" nella barra di navigazione. **Solo gli admin hanno accesso a questa funzione!**

Quando crei una pagina si apre un modulo in cui devi compilare alcuni campi:

* URL: questo campo verrà usato per visualizzare la pagina.
	Ci sono diverse categorie di pagine:

	* le pagine "About", tra cui l'informativa sulla privacy descritta più avanti, devono iniziare con '/<language-code\>/about/<page-slug\>'. Sono mostrate sul lato destro della barra di navigazione sotto l'icona a forma di punto interrogativo.
	* le pagine "Home" sono le pagine che iniziano con '/<language-code\>/home/'. Vedi [Pagina iniziale (Home)](#front-or-home-pages) più avanti
	* le pagine "Static" sono le pagine che iniziano con '/publish/'. Possono avere 2 forme:

		* /publish/<page-slug\>: il titolo di queste pagine è mostrato direttamente nel menu Pagine della barra di navigazione.
		* /publish/<menu-name\>/<page-slug\>: si tratta di menu a discesa del menu Pagine con il nome "menu-name", e il titolo di ogni pagina è mostrato nell'elenco a discesa sotto <menu-name\>.

	* le pagine messaggio, con URL che inizia con '/admin-message/', vedi [Mostrare un messaggio di amministrazione su tutte le pagine](#show-an-admin-message-on-all-pages)
	* qualsiasi altro URL può essere incluso come collegamento in altre pagine ma non sarà accessibile dalla barra dei menu.

* Titolo: è la stringa che verrà mostrata nei menu.
* Contenuto: è il contenuto della pagina. Può essere modificato con l'editor avanzato.
* Una casella di controllo chiamata "Authorize comments" è visibile ma al momento non viene usata.

## Gestione della privacy
Pagine statiche (una per lingua) che descrivono l'informativa sulla privacy del sito vengono caricate nel database durante l'installazione dell'applicazione.
Queste pagine possono essere personalizzate con la normale funzione "Edit Page" descritta sopra.

**ATTENZIONE**: non cambiare l'URL di queste pagine! Lo schema di questo URL è /<language-code\>/about/privacy-policy. Se cambi questo schema, l'informativa sulla privacy associata non sarà più accessibile!

## Piè di pagina personalizzato
Imposta `SITE_FOOTER` come spiegato in [Personalizzazione generale](settings.md/#general-customization)

## Pagine iniziali (Home)
Il tuo sito ha bisogno di due diverse pagine iniziali (dette anche home):

* la prima per le persone non autenticate, in cui puoi spiegare lo scopo del tuo sito senza dare troppi dettagli e senza nulla di privato.
* la seconda è la pagina per i tuoi membri una volta che hanno effettuato l'accesso.
Puoi modificare queste 2 pagine direttamente dalla homepage predefinita o dall'elenco delle pagine nel menu.

L'URL di queste pagine è costruito così: /<language code\>/home/authenticated e /<language code\>/home/unauthenticated.

Versioni predefinite di queste due pagine vengono caricate nel database al primo avvio.
Se il codice lingua nel .env non corrisponde a nessuna delle pagine precaricate, viene mostrata la versione en-US.

**ATTENZIONE**: non cambiare gli URL di queste pagine, altrimenti non funzioneranno!!!

## Mostrare un messaggio di amministrazione su tutte le pagine
Gli amministratori possono creare pagine particolari con un URL che inizia con '/admin-message/'. Il titolo di questa pagina verrà usato solo nell'elenco delle pagine del menu "Edit pages". Il contenuto di queste pagine è mostrato come notifica in cima a ogni pagina e può essere chiuso, ma riapparirà a ogni nuova connessione finché la pagina esiste nel database.

Puoi creare una sola pagina con URL '/admin-message/' oppure un numero qualsiasi di pagine che iniziano tutte con '/admin-message/', e ogni pagina verrà mostrata come una notifica specifica.

## Temi
Per creare il tuo tema devi applicare nuovi valori alle variabili di Bulma nel file chiamato media/public/theme.css (questo file è montato nelle immagini docker).

La personalizzazione deve avere il formato seguente:

```
:root {
	--bulma-xxx: value;
	--bulma-yyy: value;
	--bulma-zzz: value;
}
```

ad esempio

```
:root {
	--bulma-body-font-size: 16px;
	--bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
	--bulma-primary-l: 37% !important;
}
```

cambierà la dimensione globale dei caratteri del sito e cambierà il colore primario (definito in termini di HSL (Hue, Saturation, and Lightness).
(Puoi provare i colori HSL su https://hslpicker.com/)

Puoi anche cambiare queste variabili nell'ambito di un singolo componente, ma allora non si tratta più di un vero tema, vedi i dettagli su [Bulma CSS Variables](https://bulma.io/documentation/features/css-variables/) e [Customizing Bulma CSS variables](https://bulma.io/documentation/customize/with-css-variables/)

Per conoscere tutte le variabili CSS definite da Bulma, dai un'occhiata al [Bulma CSS File](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) e provale nel tuo browser per vederne l'effetto.
