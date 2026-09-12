# Ihre Website anpassen

## Einstellungen
Siehe [Einstellungen](settings.md), um die Website durch Änderung der Einstellungen anzupassen.

### Verwaltung der Funktionen
Über die Einstellungen können Sie auch die Funktionen verwalten, die den Mitgliedern angeboten werden, wie in [Verwaltung der Funktionen](settings.md/#features-management) erklärt.

### Benachrichtigungseinstellungen
Mitglieder können die Häufigkeit ihrer E-Mail-Benachrichtigungen in ihren Profileinstellungen konfigurieren. Details finden Sie unter [Funktionen – Follower & Benachrichtigungen](features.md#follower-und-benachrichtigungen).

## Seiten erstellen
Administratoren können statische Seiten mit der Funktion „Seite bearbeiten" in der Navigationsleiste erstellen oder aktualisieren. **Nur Administratoren haben Zugriff auf diese Funktion!**

Beim Erstellen einer Seite öffnet sich ein Formular, in dem Sie einige Felder ausfüllen müssen:

* URL: Dieses Feld wird verwendet, um die Seite anzuzeigen.
	Es gibt verschiedene Seitenkategorien:

	* „About“-Seiten, einschließlich der unten beschriebenen Datenschutzerklärung, müssen mit '/<language-code\>/about/<page-slug\>' beginnen. Sie werden auf der rechten Seite der Navigationsleiste unter einem Fragezeichen-Symbol angezeigt.
	* „Home“-Seiten sind Seiten, die mit '/<language-code\>/home/' beginnen. Siehe [Start- bzw. Home-Seite](#front-or-home-pages) unten
	* „Statische“ Seiten sind Seiten, die mit '/publish/' beginnen. Sie können 2 Unterformen haben:

		* /publish/<page-slug\>: Der Titel dieser Seiten wird direkt im Seiten-Menü der Navigationsleiste angezeigt.
		* /publish/<menu-name\>/<page-slug\>: Dies sind Dropdown-Menüs des Seiten-Menüs mit dem Namen „menu-name“, und der Titel jeder Seite wird in der Dropdown-Liste unter <menu-name\> angezeigt.

	* Nachrichtenseiten mit einer URL, die mit '/admin-message/' beginnt, siehe [Eine Admin-Nachricht auf allen Seiten anzeigen](#show-an-admin-message-on-all-pages)
	* Jede andere URL kann als Link in andere Seiten eingebunden werden, ist aber über die Menüleiste nicht erreichbar.

* Titel: Dies ist die Zeichenfolge, die in den Menüs angezeigt wird.
* Inhalt: Dies ist der Inhalt der Seite. Er kann mit dem Rich-Text-Editor bearbeitet werden.
* Ein Kontrollkästchen namens „Kommentare zulassen“ wird angezeigt, wird derzeit aber nicht verwendet.

## Verwaltung der Datenschutzrichtlinie
Statische Seiten (eine pro Sprache), die die Datenschutzerklärung der Website beschreiben, werden bei der Installation der Anwendung in die Datenbank geladen.
Diese Seiten können mit der oben beschriebenen Standardfunktion „Seite bearbeiten“ angepasst werden.

**WARNUNG**: Ändern Sie die URL dieser Seiten nicht! Das Muster für diese URL ist /<language-code\>/about/privacy-policy. Wenn Sie dieses Muster ändern, ist die zugehörige Datenschutzerklärung nicht mehr erreichbar!

## Eigene Fußzeile
Setzen Sie `SITE_FOOTER`, wie in [Allgemeine Anpassung](settings.md/#general-customization) erklärt.

## Start- (oder Home-)Seiten
Ihre Website benötigt zwei unterschiedliche Start- (aka Home-)Seiten:

* Die erste für nicht angemeldete Besucher, auf der Sie den Zweck Ihrer Website erklären können, ohne zu viele Details preiszugeben und ohne private Inhalte.
* Die zweite ist die Seite für Ihre Mitglieder, sobald sie angemeldet sind.
Sie können diese 2 Seiten direkt von der Standard-Startseite oder aus der Seitenliste im Menü aus bearbeiten.

Die URL dieser Seiten ist wie folgt aufgebaut: /<language code\>/home/authenticated und /<language code\>/home/unauthenticated.

Vordefinierte Versionen dieser beiden Seiten werden beim ersten Start in die Datenbank geladen.
Wenn der Sprachcode in der .env-Datei keiner der vorinstallierten Seiten entspricht, wird die en-US-Version angezeigt.

**ACHTUNG**: Ändern Sie die URLs dieser Seiten nicht, sonst funktionieren sie nicht!!!

## Eine Admin-Nachricht auf allen Seiten anzeigen
Administratoren können besondere Seiten mit einer URL erstellen, die mit '/admin-message/' beginnt. Der Titel dieser Seiten wird nur in der Seitenliste des Menüs „Seiten bearbeiten“ verwendet. Der Inhalt dieser Seiten wird als Benachrichtigung am oberen Rand jeder Seite angezeigt und kann geschlossen werden, erscheint aber bei jeder neuen Verbindung wieder, solange die Seite in der Datenbank existiert.

Sie können entweder eine Seite mit der URL '/admin-message/' oder beliebig viele Seiten erstellen, die alle mit '/admin-message/' beginnen; jede Seite wird dann als eigene Benachrichtigung angezeigt.

## Themes
Um Ihr eigenes Theme zu erstellen, müssen Sie neuen Werten für Bulma-Variablen in der Datei media/public/theme.css festlegen (diese Datei ist in den Docker-Images eingebunden).

Die Anpassung muss das folgende Format haben:

```
:root {
	--bulma-xxx: value;
	--bulma-yyy: value;
	--bulma-zzz: value;
}
```

z. B.

```
:root {
	--bulma-body-font-size: 16px;
	--bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
	--bulma-primary-l: 37% !important;
}
```

ändert die globale Schriftgröße der Website und ändert die Primärfarbe (definiert in HSL (Hue, Saturation und Lightness).
(HSL-Farben können Sie unter https://hslpicker.com/ ausprobieren)

Sie können diese Variablen auch im Gültigkeitsbereich einer Komponente ändern, aber dann ist es kein echtes Theme mehr; Details finden Sie unter [Bulma CSS Variables](https://bulma.io/documentation/features/css-variables/) und [Bulma mit CSS-Variablen anpassen](https://bulma.io/documentation/customize/with-css-variables/)

Um alle von Bulma definierten CSS-Variablen kennenzulernen, werfen Sie einen Blick in die [Bulma CSS-Datei](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) und testen Sie sie in Ihrem Browser, um die Wirkung zu sehen.
