# Design — Documentation du repo au format OKF

- **Date** : 2026-09-04
- **Statut** : approuvé par l'utilisateur (design présenté en session, section 7 ajoutée à sa demande)
- **Spec de référence** : [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) (GoogleCloudPlatform/knowledge-catalog)

## 1. Objectif

Créer, dans `docs/`, un bundle OKF v0.2 documentant le repo Cousins Matter pour
**développeurs et agents IA**. Chaque fichier `.md` du bundle porte un frontmatter
YAML dont le seul champ requis par la spec est `type`. Un seul bundle
(approche A retenue, alternatives B « multi-bundles » et C « plat » écartées).

Le bundle ne duplique pas le manuel utilisateur existant (`user-manual/`, MkDocs
sur readthedocs) : il le référence.

## 2. Arborescence (~34 fichiers)

```
docs/
  index.md              # répertoire : liens vers toutes les fiches
  log.md                # historique chronologique (plus récent d'abord)
  architecture.md       # settings/ENVIRONMENT, ASGI+Channels, Docker, WhiteNoise
  conventions.md        # services pattern, followers, feature flags, i18n, Q_SYNC
  setup-dev.md          # uv, make up4run/run/test/cover/check, ENVIRONMENT
  testing.md            # MemberTestCase, tests UI Playwright, couverture 80 %
  apps/                 # 12 fiches, une par app Django
    members.md core.md tenants.md galleries.md forum.md chat.md
    polls.md classified-ads.md pages.md troves.md genealogy.md backup.md
  modules/              # 6 fiches transverses
    followers.md notifications.md protected-media.md
    feature-flags.md themes.md management-commands.md
  flows/                # 4 flux métier bout-en-bout
    member-invitation.md gedcom-import-export.md
    gallery-bulk-import.md oauth-login.md
  specs/                # 3 specs techniques initiales (niveau dev)
    multi-tenancy.md oauth-authentication.md media-storage.md
  plan/
    roadmap.md          # travaux en cours / à venir
    debt.md             # raccourcis connus (dont classified_ads_n+1_analysis.md)
  superpowers/          # hors bundle OKF (voir §5), specs de design superpowers
```

## 3. Frontmatter commun

Champ **requis** (spec §2) : `type`.

Vocabulaire `type` du bundle : `Architecture`, `Conventions`, `Setup`,
`Testing`, `App Reference`, `Module Reference`, `Flow`, `Feature Spec`,
`Plan`, `Directory`.

Champs **recommandés** remplis systématiquement : `title`, `description`,
`tags` (liste YAML).

Cas des fichiers réservés (spec §8-9) : `index.md` porte un frontmatter
`type: Directory` (homogène, vérifié par le check) ; `log.md` n'a pas de
frontmatter — le check l'exclut comme les autres fichiers réservés, sa
structure étant imposée par la spec.

Cycle de vie : `status: draft` tant que la fiche n'est pas relue par un humain ;
`stale_after` rempli à +6 mois (voir §7). `generated: {by: claude-code,
at: <ISO 8601 Z>}` à chaque création **et** réécriture. `verified` laissé vide
(services de confiance OKF : *unverified* par défaut, *human-reviewed* plus tard).

Liens internes relatifs à la racine du bundle : `[members](/apps/members.md)`.

## 4. Contenu des fiches

- Chaque fiche cite les fichiers et symboles clés avec leurs chemins
  (`members/models.py`, `<app>/services.py`…).
- Section finale `# See also` : liens croisés apps/modules/flows connexes et
  vers les pages du user-manual quand elles existent.
- `index.md` liste toutes les fiches par sous-dossier ; `log.md` suit le format
  imposé par la spec (titres de date `YYYY-MM-DD`, plus récent d'abord).
- Les fiches reposent sur le code réel (collecte via codegraph/lectures), pas
  sur la mémoire des sessions.

## 5. Garde-fou de conformité

`make check-docs` : script Python (~15 lignes, stdlib uniquement) qui vérifie
que chaque `.md` non réservé de `docs/` a un frontmatter YAML analysable avec un
`type` non vide, que `index.md`/`log.md` ne sont pas réutilisés comme fiches,
que `stale_after` (s'il est présent) est une date, et **liste les fiches
dépassées**. La conformité OKF se réduit à ces règles (spec §11) ; aucun autre
outillage. Le check exclut `docs/superpowers/` (specs de design superpowers,
frontmatter OKF non applicable). Cible ajoutée au `check` existant.

## 6. Production

Collecte des faits par app (codegraph + lectures ciblées), rédaction fiche par
fiche, `log.md` tenu à jour au fil de l'eau. Détails (découpage, parallélisation,
ordre) dans le plan d'implémentation écrit par le skill writing-plans.

## 7. Maintien à jour

- **`stale_after` sur chaque fiche** : date ISO à partir de laquelle la fiche
  est suspecte (défaut +6 mois) ; `make check-docs` liste les fiches dépassées.
- **`generated: {by, at}` mis à jour à chaque réécriture** : l'âge réel de
  chaque fiche se lit dans son frontmatter.
- **Règle de workflow** (2 lignes dans `CLAUDE.md`) : toute PR qui modifie une
  app met à jour sa fiche (`members/` → `docs/apps/members.md`) et avance son
  `stale_after`, comme on écrit la migration.
- **`log.md`** : une entrée datée par mise à jour substantielle.
- **Point de passage à la release** : à chaque tag, traiter les fiches
  dépassées — accroché au process de release existant, pas de CI dédiée.

## 8. Hors périmètre

- Traduction du bundle (i18n) — le bundle est en anglais comme le code/user-manual.
- Génération automatique des fiches par CI ou agent périodique.
- Migration des contenus `user-manual/` (ils restent la référence utilisateur).
