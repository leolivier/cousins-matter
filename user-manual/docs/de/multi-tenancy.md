# Multi-Tenancy (mehrere Familien auf einer Bereitstellung)

Cousins Matter kann **mehrere Familien (Tenants) aus einer einzigen Bereitstellung** bedienen,
wobei die Daten jeder Familie isoliert sind. Diese Seite dokumentiert das Produktfeature und
seine Bereitstellung.

## Aktivieren des Features

Das Feature ist **standardmäßig ausgeschaltet**: Eine Bereitstellung für eine einzelne Familie
verhält sich genau wie die klassische Anwendung. Um es einzuschalten, setzen Sie in `.env`:

```
MULTI_TENANT_ENABLED=True
```

Dies bindet die `/tenants/`-URLs ein (Familien-Registrierung + Verwaltung) und zeigt den
Link „Neue Familie anlegen“ auf der Anmeldeseite. Wenn das Feature ausgeschaltet ist,
liefert all dies einen 404-Fehler.

## Konzepte

| Konzept | Wo |
|---|---|
| **Familie (Tenant)** | `tenants.Tenant` — Name, Slug, `is_active` |
| **Familien-Admin** | `Member.role = "admin"` — verwaltet die Mitglieder und Einstellungen seiner Familie |
| **Plattform-Admin** | `is_superuser` — tenant-übergreifend, wohnt auf dem `system`-Tenant, hat Zugriff auf die Django-Administration (`is_staff`) |
| **Isolation (primär)** | tenant-scope ORM-Manager (`TenantManager`) + `TenantMiddleware` |
| **Isolation (Rückfallebene)** | PostgreSQL Row-Level Security (siehe unten) |

Zwei Tenants werden durch die Migration angelegt und können nicht gelöscht werden: `default`
(zugewiesen, wenn keiner aufgelöst werden kann) und `system` (Heimat der Plattform-Admins).

## Anlegen einer Familie

* **Self-Service**: Mit aktiviertem Feature bietet die Anmeldeseite
  *„Neue Familie anlegen“* an. Der Ersteller registriert sich mit E-Mail-Verifizierung und
  wird Admin der Familie.
* **Durch einen Plattform-Admin**: `/tenants/create/` legt die Familie an und kann eine
  Einladung (mandantengebundener Link) per E-Mail an ihren ersten Admin senden.

Ein Familienkennung (Slug) wird aus dem Namen abgeleitet; reservierte Slugs
(`default`, `system`, `admin`, …) werden abgelehnt.

## Familieneinstellungen

Ein Familien-Admin bearbeitet die Einstellungen seiner Familie unter **Familieneinstellungen**
(Dropdown in der Navigationsleiste): Seitenname, Logo, Copyright, Fußzeile, Dunkelmodus,
PDF-Seitengröße, Sprache, Zeitzone, Geburtstagsvorschau, Mitgliederberechtigungen
(anlegen/einladen) und die Wurzel des Genealogie-Baums. Werte, die den globalen
Standardwerten entsprechen, werden **nicht gespeichert**, sodass eine globale Änderung weiterhin
an Familien weitergegeben wird, die sie nie überschrieben haben. E-Mails an „den Admin“
(Kontaktformular, Einladungen, Todesfallbenachrichtigungen) werden an den **Admin der Familie**
zugestellt.

## Lebenszyklus

* **Deaktivieren** (`/tenants/<slug>/toggle-active/`): Die Mitglieder der Familie werden
  abgemeldet und können sich bis zur Reaktivierung nicht mehr anmelden.
* **Endgültiges Löschen** (`/tenants/<slug>/delete/` oder `manage.py delete_tenant
  <slug>`): Entfernt die Familie und alle ihre Daten dauerhaft. Lehnt den
  System-Tenant und jede noch aktive Familie ab; erfordert die Eingabe des Slugs.

## PostgreSQL Row-Level Security (optionale Härtung)

Das ORM-Scoping ist die primäre Isolationsschicht. Als vertiefte Verteidigung (defense-in-depth)
können Sie die Datenbank selbst Cross-Tenant-Schreibvorgänge verweigern lassen:

1. Wählen Sie eine Nicht-Owner-Rolle, z. B. `cm_app`, mit einem starken Passwort.
2. Setzen Sie in `.env` `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (und
   belassen Sie `MULTI_TENANT_ENABLED=True`).
3. Führen Sie `manage.py migrate` **als Owner** aus (`POSTGRES_USER`) — die RLS-Migration
   (`tenants.0003_rls`) erstellt die Rolle, gewährt nur DML-Berechtigungen
   und die Policies. Der Container-Entrypoint erledigt dies automatisch:
   die Initialisierung läuft als Owner, nur der langlaufende Server verwendet die
   Runtime-Rolle.

Verhalten der Policies für die Runtime-Rolle:

* tenant-scope Tabellen außerhalb der eigenen Models der Apps (galleries): Zeilen außerhalb
  des Tenants der Session sind unsichtbar **und** nicht schreibbar;
* `members_member`: Lesezugriffe bleiben zulässig (die Anmeldung per E-Mail erfolgt, bevor
  ein Tenant bekannt ist), aber INSERT/UPDATE/DELETE sind strikt auf den Tenant beschränkt;
* die Middleware setzt `app.current_tenant_id` pro Anfrage und setzt es danach immer
  zurück (gepoolte Verbindungen verlieren nie einen Tenant); Plattform-Superuser erhalten
  `app.bypass`, sodass sie tenant-übergreifend administrieren können;
* Migrationen laufen als Owner, was RLS umgeht — das ist beabsichtigt und der Grund,
  warum `FORCE ROW LEVEL SECURITY` nie verwendet wird.

## Aktueller Umfang

Heute sind `members` und `galleries` tenant-scope. Die Umstellung der übrigen
Apps (chat, forum, polls, classified ads, pages, troves, genealogy) folgt
demselben Muster (`TenantModel`-Basisklasse + zusammengesetzte Indizes); bis dahin werden die
Daten dieser Apps families übergreifend innerhalb einer Bereitstellung geteilt.
