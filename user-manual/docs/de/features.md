## Funktionen

### Mitgliederverwaltung

* Mitglieder können aufgelistet, nach Vor- und Nachnamen gefiltert und sortiert werden

	![Mitglieder](assets/members.webp)

* Der Seitenadministrator oder jedes Mitglied (je nach Einstellungen) kann andere Mitglieder per E-Mail einladen

	![Einladung](assets/invite.webp)

* Jeder kann eine Einladung anfordern, die dem Seitenadministrator per E-Mail zugesandt wird, der die Person dann einladen kann. Einladungsanfragen sind durch ein Captcha geschützt.

	![Einladung anfordern](assets/request-invite.webp)

* Mitglieder können „verwaltete“ Mitglieder anlegen, d. h. Mitglieder, die auf der Website nicht aktiv sind (z. B. für kleine Kinder oder ältere Menschen)
* Verwaltete Mitglieder können von den Mitgliedern aktiviert werden, die sie verwalten (z. B. wenn ein Kind alt genug ist, um auf der Website aktiv zu sein).
* Mitglieder können in großer Menge über CSV-Dateien importiert werden
* Mitglieder können ihr eigenes Profil und die Profile der von ihnen verwalteten Mitglieder aktualisieren
* Mitglieder können als verstorben mit einem Todesdatum markiert werden (nützlich für Genealogie und Familiengeschichte)

	![Profil](assets/profile.webp)

* Ein Mitgliederverzeichnis kann im PDF-Format ausgedruckt werden

	![Verzeichnis](assets/directory.webp)

* Geburtstage der nächsten 50 Tage können angezeigt werden (50 kann in den Einstellungen geändert werden)

	![Geburtstage](assets/birthdays.webp)

### Authentifizierung

* Standard-Authentifizierung mit E-Mail und Passwort
* OAuth/SSO-Authentifizierung mit mehreren Anbietern:
	* Google
	* Facebook
	* Apple
	* GitHub
	* PocketID (selbst gehostetes OpenID Connect)
	* Jeder OpenID-Connect-kompatible Anbieter
* Detaillierte Konfiguration siehe [OAuth-Authentifizierung](oauth-authentication.md)

### Sicherheit und Anmeldehistorie

* Alle Anmeldeversuche werden automatisch mit IP-Geolokalisierung erfasst
* Die Anmeldehistorie wird zur Sicherheitsprüfung gespeichert (für Seitenadministratoren in der Django-Administration einsehbar)
* Automatisches Löschen alter Anmeldeeinträge nach einer konfigurierbaren Aufbewahrungsdauer
* Hilft Administratoren, unbefugte Zugriffsversuche zu erkennen

### Follower und Benachrichtigungen

* Mitglieder können anderen Mitgliedern folgen, um über deren Aktivitäten benachrichtigt zu werden
* Mitglieder können Chaträume, Foren, Galerien und anderen Inhalten folgen
* Automatische E-Mail-Benachrichtigungen, wenn gefolgte Inhalte aktualisiert werden
* Konfigurierbare Benachrichtigungshäufigkeit pro Mitglied:
	* **Sofort** – Benachrichtigungen werden empfangen, sobald Ereignisse eintreten
	* **Stündlich** – Empfang einer Zusammenfassung der Ereignisse jede Stunde
	* **Täglich** – Empfang einer täglichen Zusammenfassung der Ereignisse
	* **Wöchentlich** – Empfang einer wöchentlichen Zusammenfassung
	* **Monatlich** – Empfang einer monatlichen Zusammenfassung
	* **Nie** – Benachrichtigungen vollständig deaktivieren
* Jedes Mitglied kann seine bevorzugte Benachrichtigungshäufigkeit in seinen Profileinstellungen konfigurieren
* Das Zusammenfassen von Benachrichtigungen verringert die E-Mail-Flut und hält die Mitglieder trotzdem auf dem Laufenden

### Galerien

* Alle aktiven Mitglieder können Galerien erstellen und ihnen Fotos und Videos hinzufügen
* Galerien können Untergalerien in beliebiger Tiefe haben
* Fotos und Videos können in großen Mengen über Zip-Dateien importiert werden. Jeder Ordner in der Zip-Datei wird zu einer Galerie. Aktualisierungen werden verwaltet
* Die Fotoanzeige einer Galerie ist paginiert
* Fotos und Videos können im Vollbildmodus und als Diashow mit konfigurierbarer Verzögerung angezeigt werden

### Forum

* Aktive Mitglieder können Beiträge erstellen
* Aktive Mitglieder können auf Beiträge anderer Mitglieder antworten oder einfache Kommentare hinzufügen

### Chat

* Verbundene Mitglieder können im Live-Modus mit anderen verbundenen Mitgliedern chatten
* Cousins Matter verwaltet so viele Chaträume, wie gewünscht werden
* Mitglieder können private Chaträume erstellen und die Mitglieder auswählen, die an diesen Räumen teilnehmen dürfen.
	Der Ersteller des Raums wird Administrator dieses Raums und kann andere Mitglieder hinzufügen und aus diesen Mitgliedern Administratoren ernennen.
	Administratoren können andere Mitglieder und andere Administratoren einladen

### Seiten / CMS

Grundlegende CMS-Funktionen: Administratoren können statische HTML-Seiten erstellen und auf der Website veröffentlichen.
Die Startseite kann auf diese Weise konfiguriert werden, ebenso die Datenschutzerklärung, die „About“-Seiten usw.
Öffentliche Seiten (diejenigen, die über das Seiten-Menü angezeigt werden, auch wenn Sie nicht angemeldet sind) können von jedem Administrator-Mitglied erstellt und veröffentlicht werden. Ihre URL muss mit '/publish/' beginnen.
Private Seiten (diejenigen, die über das Seiten-Menü nur angezeigt werden, wenn Sie angemeldet sind) können von jedem Administrator-Mitglied erstellt und veröffentlicht werden. Ihre URL muss mit '/private/' beginnen.
Admin-Nachrichten sind eine besondere Art von Seiten, die allen verbundenen Mitgliedern am oberen Rand der Website angezeigt werden. Ihre URL muss mit '/admin-message/' beginnen.
Andere vordefinierte besondere Seiten können von jedem Administrator-Mitglied geändert werden. Sie werden über das Admin-Menü unter „Seiten bearbeiten“ aufgerufen und zeigen jeweils die Startseite, wenn Sie nicht verbunden sind (/home/unauthenticated/\<lang>), wenn Sie verbunden sind (/home/authenticated/\<lang>), sowie die Datenschutzerklärung (/about/privacy-policy/\<lang>).

### Schätze (Troves)

Dies ist ein Ort, an dem Sie die Aufmerksamkeit auf digitale Familienschätze lenken können, seien es Texte, Musik oder Videos

### Umfragen

Jedes aktive Mitglied kann eine Umfrage erstellen, und jedes aktive Mitglied kann an einer aktiven Umfrage teilnehmen.
Umfragen haben ein Veröffentlichungs- und ein Abschlussdatum. Sie können mehrere Fragen enthalten und Fragen können sein:

* einfache Ja/Nein-Fragen: das Kontrollkästchen ankreuzen
* offener Text: beliebigen Rich-Text eingeben
* Datum: ein Datum auswählen
* Auswahlmöglichkeiten: eine Auswahl aus einer Liste treffen

### Veranstaltungsplanung

Als Untermodul des Umfragemoduls kann jedes aktive Mitglied eine Umfrage zur Planung einer Veranstaltung erstellen, um festzulegen, wann eine Veranstaltung stattfinden soll. Dies ergänzt das Umfragemodul um folgende Arten von Auswahlmöglichkeiten:

* ein Datum aus einer vorgegebenen Liste auswählen
* mehrere Daten aus einer vorgegebenen Liste auswählen

### Kleinanzeigen

Jedes aktive Mitglied kann eine Kleinanzeige veröffentlichen, die von allen anderen Mitgliedern gesehen werden kann. Ist ein Mitglied an einer Anzeige interessiert, kann es eine Nachricht an den Inserenten senden, der eine E-Mail erhält.

### Genealogie

Jedes aktive Mitglied kann Personen zur Genealogie der Website hinzufügen. Sie können Personen hinzufügen, indem Sie ihre Daten in Formularen eingeben oder eine GEDCOM-Datei importieren. Die Genealogie kann im GEDCOM-Format exportiert werden. Die Genealogie kann als dynamischer Baum oder als Listen von Personen oder Familien angezeigt werden.
