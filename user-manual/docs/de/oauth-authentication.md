# OAuth/SSO-Authentifizierung

## Einführung

Cousins Matter unterstützt die Authentifizierung über OAuth2/OpenID Connect mit mehreren Anbietern. Dies ermöglicht es Mitgliedern, sich mit ihren bestehenden Konten bei gängigen Diensten wie Google, Facebook, GitHub und weiteren anzumelden.
**WICHTIG**: Die Verknüpfung zwischen dem Konto beim OAuth-Identitätsanbieter und Cousins Matter wird über die E-Mail-Adresse des Mitglieds hergestellt.

## Voraussetzungen

* Mitglieder müssen eine gültige Einladung besitzen, um sich über OAuth zu registrieren
* Die OAuth-Anbieter müssen in der `.env`-Datei konfiguriert sein
* Jeder Anbieter erfordert eine Client-ID und ein Client-Secret

## Konfiguration

### OAuth-Anbieter aktivieren

Definieren Sie in Ihrer `.env`-Datei die Liste der Anbieter, die Sie aktivieren möchten:

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Verfügbare Anbieter:
* `google` - Google OAuth
* `facebook` - Facebook OAuth
* `apple` - Apple Sign In
* `github` - GitHub OAuth
* `pocketid` - PocketID (OpenID Connect)
* Jeder andere OpenID-Connect-kompatible Anbieter

### Auto-Signup-Konfiguration

Steuern Sie, ob Benutzer ihre Anmeldung bei der Verwendung von OAuth bestätigen müssen:

```bash
# Bestätigung erforderlich (aus Sicherheitsgründen empfohlen)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Automatische Registrierung ohne Bestätigung erlauben
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Standard:** `False` (Bestätigung erforderlich)

## Anbieter-spezifische Konfiguration

### Google OAuth

1. Erstellen Sie ein Projekt in der [Google Cloud Console](https://console.cloud.google.com/)
2. Aktivieren Sie die Google+ API
3. Erstellen Sie OAuth-2.0-Anmeldeinformationen
4. Fügen Sie autorisierte Redirect-URIs hinzu: `https://yourdomain.com/accounts/google/login/callback/`

Konfiguration in `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### Facebook OAuth

1. Erstellen Sie eine App unter [Facebook Developers](https://developers.facebook.com/)
2. Fügen Sie das Produkt Facebook Login hinzu
3. Konfigurieren Sie die gültigen OAuth-Redirect-URIs: `https://yourdomain.com/accounts/facebook/login/callback/`

Konfiguration in `.env`:
```bash
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret
```

### Apple Sign In

1. Registrieren Sie Ihre App im [Apple Developer Portal](https://developer.apple.com/)
2. Erstellen Sie eine Service ID
3. Konfigurieren Sie Sign In with Apple

Konfiguration in `.env`:
```bash
APPLE_OAUTH_CLIENT_ID=your_apple_service_id
APPLE_OAUTH_CLIENT_SECRET=your_apple_client_secret
```

### GitHub OAuth

1. Registrieren Sie eine neue OAuth-Anwendung in den [GitHub-Einstellungen](https://github.com/settings/developers)
2. Setzen Sie die Authorization-callback-URL: `https://yourdomain.com/accounts/github/login/callback/`

Konfiguration in `.env`:
```bash
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

### PocketID (OpenID Connect)

[PocketID](https://pocketid.app/) ist ein selbst gehosteter OpenID-Connect-Anbieter.

Konfiguration in `.env`:
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

### Generischer OpenID-Connect-Anbieter

Für jeden anderen OpenID-Connect-kompatiblen Anbieter:

Konfiguration in `.env`:
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=your_client_id
OPENID_CONNECT_OAUTH_CLIENT_SECRET=your_client_secret
```

## Einladungsverfahren

Die OAuth-Authentifizierung in Cousins Matter erfordert eine gültige Einladung:

1. **Für neue Benutzer:**
   * Ein Administrator oder ein berechtigtes Mitglied muss eine Einladung an die E-Mail-Adresse des Benutzers senden
   * Der Benutzer klickt auf den Einladungslink
   * Die Einladung wird in der Session gespeichert
   * Der Benutzer kann sich dann über OAuth authentifizieren
   * Das Konto wird automatisch aktiviert

2. **Für bestehende inaktive Benutzer:**
   * Wenn ein Benutzerkonto existiert, aber nicht aktiv ist
   * Muss der Benutzer den per E-Mail gesendeten Einladungslink verwenden
   * Nach dem Klick auf den Link kann er sich über OAuth authentifizieren
   * Das Konto wird aktiviert und mit dem OAuth-Anbieter verknüpft

3. **Für aktive Benutzer:**
   * Aktive Benutzer können sich direkt über OAuth anmelden
   * Eine Einladung ist nicht erforderlich
   * Das OAuth-Konto wird mit ihrem bestehenden Konto verknüpft

## Sicherheitsaspekte

* **E-Mail-Verifizierung:** OAuth-Anbieter müssen eine E-Mail-Adresse liefern
* **Einladung erforderlich:** Neue Benutzer können sich ohne Einladung nicht selbst registrieren
* **Session-Sicherheit:** Einladungs-Token werden sicher in der Session gespeichert
* **Token-Ablauf:** Einladungs-Token laufen nach einer konfigurierbaren Zeit ab (siehe `MAX_REGISTRATION_AGE` in [Einstellungen](settings.md))

## Fehlerbehebung

### „No invitation found for this email address“

Dieser Fehler tritt auf, wenn:
* Der Benutzer nicht auf einen Einladungslink geklickt hat
* Die Einladung abgelaufen ist
* Die E-Mail-Adresse des OAuth-Anbieters nicht mit der eingeladenen E-Mail-Adresse übereinstimmt

**Lösung:** Fordern Sie eine neue Einladung von einem Administrator mit der richtigen E-Mail-Adresse an.

### „The identity provider did not provide an email address“

Manche OAuth-Anbieter geben die E-Mail-Adresse möglicherweise nicht weiter.

**Lösung:** Konfigurieren Sie den OAuth-Anbieter so, dass die E-Mail-Adresse im Scope enthalten ist.

### „This account is not yet active“

Das Benutzerkonto existiert, wurde aber noch nicht aktiviert.

**Lösung:** Verwenden Sie den per E-Mail gesendeten Einladungslink, bevor Sie versuchen, sich über OAuth anzumelden.

## Neustart erforderlich

Starten Sie Cousins Matter nach dem Ändern der OAuth-Einstellungen in `.env` neu:

```bash
docker compose restart
```

## Siehe auch

* [Einstellungen](settings.md) - Vollständige Referenz der Einstellungen
* [Installation](installation.md) - Erstkonfiguration
* [Funktionen](features.md) - Funktionen der Mitgliederverwaltung
