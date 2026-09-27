# Multi-tenants (plusieurs familles sur un même déploiement)

Cousins Matter peut prendre en charge **plusieurs familles (tenants) à partir d’un seul déploiement**,
les données de chaque famille étant isolées. Cette page décrit cette fonctionnalité du produit et
son déploiement.

## Activation de la fonctionnalité

La fonctionnalité est **désactivée par défaut** : un déploiement pour une seule famille se comporte exactement
comme l’application classique. Pour l’activer, définissez dans `.env` :

```
MULTI_TENANT_ENABLED=True
```

Cela monte les URL `/tenants/` (inscription et gestion des familles) et affiche le
lien « Créer une nouvelle famille » sur la page de connexion. Lorsque cette fonctionnalité est désactivée, toutes ces URL renvoient une erreur 404.

## Concepts

| Concept | Où |
|---|---|
| **Famille (locataire)** | `tenants.Tenant` — nom, slug, `is_active` |
| **Administrateur de famille** | `Member.role = « admin »` — gère les membres et les paramètres de sa famille |
| **Administrateur de la plateforme** | `is_superuser` — inter-tenants, réside sur le locataire `system`, accès Django-admin (`is_staff`) |
| **Isolation (primaire)** | gestionnaire ORM au niveau du locataire (`TenantManager`) + `TenantMiddleware` |
| **Isolation (filet de sécurité)** | Sécurité au niveau des lignes dans PostgreSQL (voir ci-dessous) |

Deux tenants sont créés par migration et ne peuvent pas être supprimés : `default`
(attribué lorsqu’aucun autre ne peut être résolu) et `system` (siège des administrateurs de la plateforme).

## Création d’une famille

* **En libre-service** : lorsque la fonctionnalité est activée, la page de connexion propose
  *« Créer une nouvelle famille »*. Le créateur s’inscrit via une vérification par e-mail et
  devient l’administrateur de la famille.
* **Par un administrateur de la plateforme** : `/tenants/create/` crée la famille et permet d’envoyer par e-mail
  une invitation (lien lié au locataire) à son premier administrateur.

Un identifiant de famille (slug) est dérivé de son nom ; les slugs réservés
(`default`, `system`, `admin`, …) sont rejetés.

## Se connecter à une famille

Tout le monde se connecte sur la page de connexion standard — la famille est résolue
automatiquement à partir du compte connecté ; il n’existe pas d’URL propre à chaque famille.
Une adresse e-mail appartient à une seule famille : pour rejoindre une autre famille,
il faut une autre adresse e-mail.

* **Créateur de la famille** : après l’inscription via *« Créer une nouvelle famille »*,
  le compte reste inactif tant que le lien de l’e-mail de vérification n’a pas été cliqué ;
  connectez-vous ensuite normalement et vous êtes l’administrateur de la famille.
* **Autres membres** : soit accepter l’invitation envoyée par e-mail par l’administrateur
  de la famille (lien lié au locataire → inscription → vérification par e-mail), soit soumettre
  une demande d’adhésion (formulaire avec captcha) qu’un administrateur de la famille doit approuver.
  Dans les deux cas, connectez-vous ensuite sur la page de connexion standard.

## Paramètres de la famille

Un administrateur de famille modifie les paramètres de sa famille dans **Paramètres de la famille**
(menu déroulant de la barre de navigation) : nom du site, logo, mentions de copyright, pied de page, mode sombre, taille de page PDF
, langue, fuseau horaire, prévision des anniversaires, autorisations des membres
(créer/inviter) et la racine de l’arbre généalogique. Les valeurs égales aux
valeurs par défaut globales ne sont **pas enregistrées** ; ainsi, une modification globale se répercute toujours sur les familles
qui ne les ont jamais remplacées. Les e-mails destinés à « l’administrateur » (formulaire de contact, invitations,
notifications de décès) sont redirigés vers l’**administrateur de la famille**.

## Cycle de vie

* **Désactiver** (`/tenants/<slug>/toggle-active/`) : les membres de la famille sont
  déconnectés et ne peuvent pas se reconnecter tant que la famille n’est pas réactivée.
* **Suppression définitive** (`/tenants/<slug>/delete/`, ou `manage.py delete_tenant
  <slug>`) : supprime définitivement la famille et toutes ses données. Refuse le
  locataire système et toute famille encore active ; nécessite la saisie du slug.

## Sécurité au niveau des lignes dans PostgreSQL (renforcement facultatif)

La portée de l’ORM constitue la principale couche d’isolation. Pour une défense en profondeur, vous pouvez
faire en sorte que la base de données elle-même refuse les écritures inter-tenants. Le RLS est actif lorsque
`MULTI_TENANT_ENABLED=True` **et** que `POSTGRES_RUNTIME_USER` est défini.

**Avec Docker**, définissez dans `.env` :

```
MULTI_TENANT_ENABLED=True
POSTGRES_RUNTIME_USER=cm_app
POSTGRES_RUNTIME_PASSWORD=<mot de passe fort>
```

puis redémarrez les conteneurs applicatifs :

```
docker compose restart cousins-matter qcluster
```

Au démarrage, le point d’entrée exécute les migrations **en tant que propriétaire**
(`POSTGRES_USER`) : la migration RLS (`tenants.0003_rls`) crée le rôle d’exécution avec des
privilèges DML uniquement et applique les politiques, puis le serveur et qcluster redémarrent
et se connectent avec le rôle d’exécution. Rien à exécuter à la main.

**Avec une installation manuelle (sans Docker)**, définissez les mêmes variables et exécutez
`manage.py migrate` **en tant que propriétaire** (`POSTGRES_USER`) — c’est exactement ce que
le point d’entrée automatise ci-dessus.

**À quoi sert `POSTGRES_USER`** : c’est le propriétaire (superutilisateur) créé par l’image
PostgreSQL. Il exécute les migrations — création du rôle d’exécution, de ses privilèges DML et
des politiques — et, en tant que propriétaire, il contourne entièrement le RLS ; c’est la raison
pour laquelle `FORCE ROW LEVEL SECURITY` n’est jamais utilisé. Le serveur et qcluster n’y
recourent qu’en repli, lorsque `POSTGRES_RUNTIME_USER` n’est pas défini (le RLS est alors sans effet).

Comportement des politiques pour le rôle d’exécution :

* toutes les tables relevant du périmètre d’un locataire (galeries, chat, forum, petites annonces,
  sondages, troves, généalogie, pages) : les lignes n’appartenant pas au locataire de la session
  sont invisibles **et** non modifiables ;
* `members_member` : les lectures restent autorisées (la connexion par e-mail a lieu avant que le
  locataire ne soit connu), mais les opérations INSERT/UPDATE/DELETE sont strictement limitées au périmètre du locataire ;
* le middleware définit `app.current_tenant_id` à chaque requête et le réinitialise
  toujours par la suite (les connexions mises en pool ne divulguent jamais de locataire) ; les superutilisateurs de la plateforme
  disposent de `app.bypass` afin de pouvoir administrer les tenants de manière transversale ;
* les migrations s’exécutent en tant que propriétaire, ce qui contourne le RLS — ceci est voulu, et c’est la
  raison pour laquelle `FORCE ROW LEVEL SECURITY` n’est jamais utilisé.

## Portée actuelle

Toutes les applications du produit ont une portée au niveau du locataire et sont couvertes par la
sécurité au niveau des lignes : `members`, `galleries`, `chat`, `troves`, `forum`, `classified ads`,
`polls`, `genealogy` et `pages` — 22 tables, migrations `tenants.0003_rls` à `tenants.0010_rls_pages`.
Seules les tables d’infrastructure (sessions Django, comptes allauth) restent globales ; le
périmétrage par l’ORM s’applique à tout le reste.
