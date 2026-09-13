# Migration de la version 1 à la version 2

## Introduction

La version 2 de Cousins Matter est une refonte majeure de la version 1 et n’est pas directement compatible avec celle-ci.
Parmi les principaux changements, on peut citer :

* la base de données a été migrée de SQLite3 vers PostgreSQL afin d’améliorer les performances et l’évolutivité.
* Cousins Matter est désormais composé d’au moins 4 conteneurs Docker :

    * le serveur web
    * la base de données
    * Redis
    * le serveur de tâches asynchrones

    et nécessitera donc Docker Compose pour fonctionner.

## Prérequis

Vous devez avoir installé et configuré Cousins Matter v1 sur votre système.

Vous aurez également besoin d’un environnement Python 3.14 ou supérieur pour exécuter le script de migration.

## Procédure

1. Arrêtez Cousins Matter v1

    ```
    cd <répertoire-cousins-matter-v1>
    docker compose down
    ```

1. Téléchargez le script d’administration de Cousins Matter

	Veuillez remplacer dans le lien ci-dessous le paramètre <release\> par la version actuelle de Cousins Matter :
![Version GitHub](https://img.shields.io/github/v release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
    mkdir scripts
    curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<version>/scripts/manage_cousins_matter.py
    ```

1. Exécutez le script de migration

	```
    python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <version>]
    ```

    Si aucune version n’est spécifiée, la migration s’effectuera vers la dernière version de la v2.X (recommandé).

    **Surveillez attentivement le journal du script de migration !** Il vous indiquera la progression de la migration ainsi que les éventuels problèmes ou actions à entreprendre.

1. Mettez à jour vos paramètres

    Les paramètres de Cousins Matter v2 sont différents de ceux de la v1. Veuillez mettre à jour votre fichier .env afin qu’il corresponde aux paramètres de Cousins Matter v2.

    Les paramètres de Cousins Matter v2 sont détaillés sur la page [Paramètres](settings.md).
    La migration met notamment à jour le fichier .env.example afin qu’il corresponde aux paramètres de Cousins Matter v2. Veuillez donc comparer ce nouveau fichier .env.example avec votre fichier .env et mettre à jour ce dernier en conséquence.

    Notez également que certaines valeurs par défaut ont changé. Par exemple :

    * ALLOW_MEMBERS_TO_CREATE_MEMBERS et ALLOW_MEMBERS_TO_INVITE_MEMBERS sont désormais définis sur True par défaut
	* ALLOWED_HOSTS contient désormais la valeur de SITE_DOMAIN (« 127.0.0.1,localhost,$SITE_DOMAIN ») par défaut
    * DARK_MODE est désormais défini sur False par défaut
    * SESSION_COOKIE_DOMAIN est désormais défini sur .$SITE_DOMAIN par défaut
	* SITE_PORT est désormais défini sur 0 si SITE_DOMAIN est défini, et sur 8000 dans le cas contraire

De plus, de nouvelles variables ont été ajoutées au fichier .env, mais elles ont des valeurs par défaut appropriées.

    * POSTGRES_USER=cousinsmatter
    * POSTGRES_DB=cousinsmatter
    * POSTGRES_HOST=postgres
    * POSTGRES_PASSWORD est calculé automatiquement lors de la migration
    * PREVIOUS_SECRET_KEYS est calculé automatiquement lors de la migration (et la clé SECRET_KEY est renouvelée)

1. Démarrer Cousins Matter v2

    ```
    docker compose pull  # récupérer toutes les images
    docker compose up -d
    ```
