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
faire en sorte que la base de données elle-même refuse les écritures inter-tenants :

1. Choisissez un rôle autre que celui de propriétaire, par exemple `cm_app`, avec un mot de passe fort.
2. Dans `.env`, définissez `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (et
   conservez `MULTI_TENANT_ENABLED=True`).
3. Exécutez `manage.py migrate` **en tant que propriétaire** (`POSTGRES_USER`) — la migration RLS
   (`tenants.0003_rls`) crée le rôle, accorde des privilèges DML uniquement
   et applique les politiques. Le point d’entrée du conteneur s’en charge automatiquement :
   l’initialisation s’exécute en tant que propriétaire, seul le serveur à exécution prolongée utilise le
   rôle d’exécution.

Comportement des politiques pour le rôle d’exécution :

* tables relevant du périmètre d’un locataire en dehors des modèles propres aux applications (galeries) : les lignes n’appartenant pas
  au locataire de la session sont invisibles **et** non modifiables ;
* `members_member` : les lectures restent autorisées (la connexion par e-mail a lieu avant que le
  locataire ne soit connu), mais les opérations INSERT/UPDATE/DELETE sont strictement limitées au périmètre du locataire ;
* le middleware définit `app.current_tenant_id` à chaque requête et le réinitialise
  toujours par la suite (les connexions mises en pool ne divulguent jamais de locataire) ; les superutilisateurs de la plateforme
  disposent de `app.bypass` afin de pouvoir administrer les tenants de manière transversale ;
* les migrations s’exécutent en tant que propriétaire, ce qui contourne le RLS — ceci est voulu, et c’est la
  raison pour laquelle `FORCE ROW LEVEL SECURITY` n’est jamais utilisé.

## Portée actuelle

Aujourd’hui, `members` et `galleries` ont une portée au niveau du locataire. La conversion des autres
applications (chat, forum, sondages, petites annonces, pages, troves, généalogie) suit
le même modèle (classe de base `TenantModel` + index composites) ; d’ici là, les
données de ces applications sont partagées entre les familles d’un déploiement.
