# Autenticazione OAuth/SSO

## Introduzione

Cousins Matter supporta l'autenticazione tramite OAuth2/OpenID Connect con più provider. Questo permette ai membri di accedere usando i loro account già esistenti presso servizi diffusi come Google, Facebook, GitHub e altri.
**IMPORTANTE**: il collegamento tra l'account del provider di identità OAuth e Cousins Matter è stabilito usando l'indirizzo email del membro.

## Prerequisiti

* I membri devono avere un invito valido per registrarsi tramite OAuth
* I provider OAuth devono essere configurati nel file `.env`
* Ogni provider richiede un client ID e un client secret

## Configurazione

### Attivare i provider OAuth

Nel tuo file `.env`, definisci l'elenco dei provider che vuoi attivare:

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Provider disponibili:
* `google` - Google OAuth
* `facebook` - Facebook OAuth
* `apple` - Apple Sign In
* `github` - GitHub OAuth
* `pocketid` - PocketID (OpenID Connect)
* Qualsiasi altro provider compatibile con OpenID Connect

### Configurazione dell'iscrizione automatica

Controlla se gli utenti debbano confermare il proprio accesso quando usano OAuth:

```bash
# Richiedi la conferma (consigliato per la sicurezza)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Consenti l'iscrizione automatica senza conferma
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Valore predefinito:** `False` (è richiesta la conferma)

## Configurazione specifica per provider

### Google OAuth

1. Crea un progetto in [Google Cloud Console](https://console.cloud.google.com/)
2. Attiva l'API Google+
3. Crea credenziali OAuth 2.0
4. Aggiungi gli URI di reindirizzamento autorizzati: `https://yourdomain.com/accounts/google/login/callback/`

Configurazione in `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### Facebook OAuth

1. Crea un'app in [Facebook Developers](https://developers.facebook.com/)
2. Aggiungi il prodotto Facebook Login
3. Configura i Valid OAuth Redirect URIs: `https://yourdomain.com/accounts/facebook/login/callback/`

Configurazione in `.env`:
```bash
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret
```

### Apple Sign In

1. Registra la tua app in [Apple Developer Portal](https://developer.apple.com/)
2. Crea un Service ID
3. Configura Sign In with Apple

Configurazione in `.env`:
```bash
APPLE_OAUTH_CLIENT_ID=your_apple_service_id
APPLE_OAUTH_CLIENT_SECRET=your_apple_client_secret
```

### GitHub OAuth

1. Registra una nuova applicazione OAuth in [GitHub Settings](https://github.com/settings/developers)
2. Imposta l'Authorization callback URL: `https://yourdomain.com/accounts/github/login/callback/`

Configurazione in `.env`:
```bash
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

### PocketID (OpenID Connect)

[PocketID](https://pocketid.app/) è un provider OpenID Connect self-hosted.

Configurazione in `.env`:
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

### Provider OpenID Connect generico

Per qualsiasi altro provider compatibile con OpenID Connect:

Configurazione in `.env`:
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=your_client_id
OPENID_CONNECT_OAUTH_CLIENT_SECRET=your_client_secret
```

## Processo di invito

L'autenticazione OAuth in Cousins Matter richiede un invito valido:

1. **Per i nuovi utenti:**
   * Un amministratore o un membro autorizzato deve inviare un invito all'email dell'utente
   * L'utente clicca sul link di invito
   * L'invito è conservato nella sessione
   * L'utente può quindi autenticarsi tramite OAuth
   * L'account viene attivato automaticamente

2. **Per gli utenti esistenti non attivi:**
   * Se un account utente esiste ma non è attivo
   * L'utente deve usare il link di invito inviato alla sua email
   * Dopo aver cliccato sul link, può autenticarsi tramite OAuth
   * L'account viene attivato e collegato al provider OAuth

3. **Per gli utenti attivi:**
   * Gli utenti attivi possono accedere direttamente tramite OAuth
   * Non è richiesto alcun invito
   * L'account OAuth viene collegato al loro account esistente

## Considerazioni sulla sicurezza

* **Verifica dell'email:** i provider OAuth devono fornire un indirizzo email
* **Invito obbligatorio:** i nuovi utenti non possono registrarsi da soli senza un invito
* **Sicurezza della sessione:** i token di invito sono conservati in modo sicuro nella sessione
* **Scadenza dei token:** i token di invito scadono dopo un periodo configurabile (vedi `MAX_REGISTRATION_AGE` in [Impostazioni](settings.md))

## Risoluzione dei problemi

### "No invitation found for this email address"

Questo errore si verifica quando:
* L'utente non ha cliccato su un link di invito
* L'invito è scaduto
* L'email fornita dal provider OAuth non corrisponde all'email invitata

**Soluzione:** richiedi un nuovo invito a un amministratore con l'indirizzo email corretto.

### "The identity provider did not provide an email address"

Alcuni provider OAuth potrebbero non condividere l'indirizzo email.

**Soluzione:** configura il provider OAuth per includere l'email nello scope.

### "This account is not yet active"

L'account utente esiste ma non è stato attivato.

**Soluzione:** usa il link di invito ricevuto via email prima di tentare l'accesso tramite OAuth.

## Riavvio necessario

Dopo aver modificato le impostazioni OAuth in `.env`, riavvia Cousins Matter:

```bash
docker compose restart
```

## Vedi anche

* [Impostazioni](settings.md) - riferimento completo alle impostazioni
* [Installazione](installation.md) - configurazione iniziale
* [Funzionalità](features.md) - funzionalità di gestione dei membri
