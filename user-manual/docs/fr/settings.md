# Paramètres

## Introduction

Les paramètres de Cousins Matter peuvent être gérés à l'aide d'un fichier `.env` situé dans le répertoire principal de l'application.

Si vous avez utilisé le script `manage_cousins_matter.py` pour installer Cousins Matter comme décrit dans la section [Installation](installation.md), un fichier `.env` d'exemple a été téléchargé automatiquement pour vous et les variables `SECRET_KEY` et `POSTGRES_PASSWORD` ont été générées automatiquement (**ne les écrasez pas !**).

Si vous travaillez à partir du code source, copiez le fichier `.env.example` dans `.env`.

Dans les deux cas, vous devez maintenant modifier le fichier `.env` pour définir les propriétés en fonction de votre contexte, comme décrit ci-dessous.

De nombreux paramètres sont disponibles pour personnaliser la partie technique de votre site…

N’oubliez pas non plus de consulter la section [Personnalisation](customizing.md) pour personnaliser l’apparence et l’ergonomie de votre site.

**AVERTISSEMENT** : si le conteneur est déjà en cours d’exécution, la mise à jour des paramètres dans `.env` ne sera prise en compte qu’après son redémarrage.
Pour ce faire, il suffit d’exécuter la commande suivante (dans le répertoire du site) :
```
docker compose restart
```

## Sécurité

* `SECRET_KEY` : une clé secrète qui protège votre site. Elle doit être extrêmement complexe et rester confidentielle ! Le moyen le plus simple de la générer est d’exécuter `python manage_cousins_matter.py rotate-secrets`. Ce script mettra également à jour les variables PREVIOUS_SECRET_KEYS dans le fichier .env. Ces variables servent à décoder les jetons qui ont été envoyés aux membres avec la clé secrète précédente.

	_(Encore une fois, si vous avez utilisé `manage_cousins_matter.py` pour installer Cousins Matter, cette clé a déjà été générée pour vous ; ne la remplacez pas)_
* `MAX_REGISTRATION_AGE` : durée de validité maximale en secondes des jetons d’invitation ; la valeur par défaut est de 2 jours (2*24*3600)

## Superutilisateur

Avant d’exécuter `docker compose up -d` pour la première fois, fournissez les informations nécessaires à la création du superutilisateur (c’est-à-dire le compte administrateur).

* `ADMIN` : le nom du compte du superutilisateur
* `ADMIN_PASSWORD` : le mot de passe du superutilisateur
* `ADMIN_EMAIL` : l’adresse e-mail du superutilisateur
* `ADMIN_FIRSTNAME` : le prénom du superutilisateur
* `ADMIN_LASTNAME` : le nom de famille du superutilisateur

**TOUTES CES VARIABLES SONT OBLIGATOIRES POUR CRÉER LE COMPTE DE SUPERUTILISATEUR ET N’ONT PAS DE VALEURS PAR DÉFAUT**

## Gestion des fonctionnalités

Vous pouvez gérer les fonctionnalités qui seront proposées aux membres dans le fichier .env.

Pour ce faire, modifiez la variable FEATURES_FLAGS en vous basant sur le contenu du fichier .env.example et définissez la valeur de chaque fonctionnalité à ignorer sur « false ».

La valeur par défaut de FEATURES_FLAGS est :
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True; show_public_chats=True;show_private_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_site_stats=True;show_export_members=True;show_change_language=True;show_genealogy=True"
```

**Indicateurs de fonctionnalités disponibles :**

* `show_birthdays_in_homepage` : affiche les anniversaires à venir sur la page d'accueil pour les membres authentifiés
* `show_galleries` : active la fonctionnalité de galeries de photos et de vidéos
* `show_forums` : active les discussions sur les forums
* `show_public_chats` : active les salons de discussion publics
* `show_private_chats` : active les salons de discussion privés
* `show_classified_ads` : active la fonctionnalité des petites annonces
* `show_polls` : active la fonctionnalité des sondages
* `show_event_planners` : active les sondages de planification d'événements (sondages de sélection de date)
* `show_pages` : active la fonctionnalité des pages CMS
* `show_treasures` : active la fonctionnalité des « trésors » (trésors de famille)
* `show_site_stats` : affiche la page des statistiques du site
* `show_export_members` : autorise l'exportation de l'annuaire des membres au format PDF
* `show_change_language` : autorise le changement de langue dans l'interface
* `show_genealogy` : active les fonctionnalités de généalogie (arbres généalogiques, importation/exportation GEDCOM)

**AVERTISSEMENTS :**

1. La variable INCLUDE_BIRTHDAYS_IN_HOMEPAGE a été remplacée par l’indicateur de fonctionnalité show_birthdays_in_homepage, comme indiqué ci-dessus.
2. La variable FEATURES_FLAGS doit figurer sur une seule ligne dans le fichier .env. Tous les indicateurs sont séparés par des points-virgules. Si vous définissez cette variable dans votre fichier .env et qu’un indicateur n’apparaît pas dans la liste, il est considéré comme faux.

## Personnalisation générale

### Site

* `SITE_NAME` : le nom du site ; la valeur par défaut est « Cousins Matter ! ».
* `SITE_DOMAIN` : le domaine du site, par exemple myfamily.com ; aucune valeur par défaut.
* `SITE_FOOTER` : le pied de page facultatif du site, par exemple « Le réseau social de la famille Simpson ».
* `SITE_LOGO` : l’URL relative facultative du logo de votre site (dans le coin supérieur gauche). Doit avoir un rapport d’aspect de 4:1. **DOIT ÊTRE ENREGISTRÉ DANS** le dossier « media/public » de votre site ; **l’URL doit donc commencer par « /media/public »** (par exemple : SITE_LOGO = « /media/public/my-own-logo.jpg »)
* `SITE_COPYRIGHT` : les mentions de copyright de votre site, par exemple « Copyright © 2024 Cousins Matter ».
* `DARK_MODE` : active le thème en mode sombre. La valeur par défaut est False.


### Membres

* `ALLOW_MEMBERS_TO_CREATE_MEMBERS` : la valeur par défaut est « True ». Pour empêcher les membres de créer et de gérer d'autres membres, définissez cette option sur « False » ; seuls les administrateurs pourront alors le faire.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS` : la valeur par défaut est True. Pour empêcher les membres d’inviter d’autres membres à rejoindre le site, définissez cette option sur False ; seuls les administrateurs pourront alors le faire.
* `BIRTHDAY_DAYS` : nombre de jours à venir pour afficher les anniversaires ; la valeur par défaut est 50
* ~~`INCLUDE_BIRTHDAYS_IN_HOMEPAGE`~~ : **OBSOLÈTE** - Utilisez plutôt `show_birthdays_in_homepage` dans `FEATURES_FLAGS`
* `PDF_SIZE` : format de page PDF pour l'annuaire imprimé. Format « A4 » ou « letter ». La valeur par défaut est A4.
* `MAX_CSV_FILE_SIZE`(*): Taille maximale du fichier CSV d’importation des membres ; la valeur par défaut est 2 Mo.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP` : Saisissez ici l’adresse IP externe de votre serveur. Elle est utilisée pour la trace de connexion lorsque celle-ci provient du réseau interne. La valeur par défaut est « 8.8.8.8 ».
* `LOGIN_HISTORY_PURGE_DAYS` : nombre de jours pendant lesquels l'historique des connexions est conservé (visible par les administrateurs dans l'interface d'administration Django), la valeur par défaut est 365.

### Galeries

* `DEFAULT_GALLERY_PAGE_SIZE` : nombre de photos par page de galerie (modifiable à l'écran), la valeur par défaut est 25
* `MAX_PHOTO_FILE_SIZE`(*): Taille maximale de chaque photo ; la valeur par défaut est 5 Mo
* `MAX_VIDEO_FILE_SIZE`(*): Taille maximale de chaque vidéo ; la valeur par défaut est 20 Mo
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): Taille maximale du fichier ZIP de téléchargement groupé des galeries ; la valeur par défaut est 20 Mo
* `SLIDESHOW_DELAY` : délai en secondes entre chaque photo d'un diaporama ; valeur par défaut : 5

### Messages et discussions

* `MESSAGE_MAX_SIZE`(*): taille maximale d'un message sur le forum ou dans les discussions (notez qu'il peut contenir une photo) ; valeur par défaut : 2,5 Mo.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): Taille maximale d’un commentaire associé à un message sur le forum ou dans les discussions ; la valeur par défaut est de 1 000
* `CONTACT_MAX_SIZE`(*): Taille maximale d’un message de contact ; la valeur par défaut est de 1 Mo

### Pages

* `PAGE_MAX_SIZE`(*): Taille maximale d'une page simple ; la valeur par défaut est de 10 Mo

### Sondages

* `POLL_MAX_SIZE`(*): Taille maximale d'un sondage ; la valeur par défaut est de 1 Mo

### Petites annonces

* `CLASSIFIED_AD_MAX_SIZE`(*): Taille maximale d'une petite annonce ; la valeur par défaut est de 1 Mo

### Collections

* `TROVE_FILE_MAX_SIZE`(*): Taille maximale d'un fichier de collection ; la valeur par défaut est de 20 Mo
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): Taille maximale d'une image de collection ; la valeur par défaut est de 5 Mo
* `TROVE_THUMBNAIL_SIZE`(*): Taille maximale d’une vignette de fichier Trove en pixels ; valeur par défaut : 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): Nombre par défaut de fichiers Trove par page ; valeur par défaut : 10

### Petites annonces

* `MAX_PHOTO_PER_AD`: Nombre maximal de photos par petite annonce ; valeur par défaut : 10

### Généalogie

* `FAMILY_CHART_GENERATIONS` : nombre de générations à afficher en amont et en aval de la personne centrale dans l’arbre généalogique ; valeur par défaut : 4
* `FAMILY_CHART_ROOT_PERSON_ID` : identifiant par défaut de la personne racine à afficher dans l’arbre généalogique si aucun n’est spécifié ; valeur par défaut : l’identifiant de la première personne de la base de données
* `GEDCOM_FILE` : fichier GEDCOM à utiliser pour l'exportation de la généalogie ; la valeur par défaut est « genealogy.ged »

## Authentification OAuth/SSO

* `OAUTH_PROVIDERS` : liste, séparée par des virgules, des fournisseurs OAuth à activer. Fournisseurs disponibles : `google`, `facebook`, `apple`, `github`, `pocketid` ou tout fournisseur `openid_connect`. Par défaut, cette liste est vide (OAuth non activé).
* `SOCIALACCOUNT_AUTO_SIGNUP` : indique s’il faut demander une confirmation lorsqu’un utilisateur se connecte via un fournisseur OAuth. La valeur par défaut est False (confirmation requise).

Pour chaque fournisseur, vous devez définir :
* `<PROVIDER>_OAUTH_CLIENT_ID` : identifiant client OAuth du fournisseur
* `<PROVIDER>_OAUTH_CLIENT_SECRET` : secret client OAuth du fournisseur

Pour les fournisseurs OpenID Connect (y compris PocketID) :
* `<PROVIDER>_SERVER_URL` : URL du serveur OpenID Connect

**Exemple de configuration :**
```
OAUTH_PROVIDERS=google,github,pocketid
GOOGLE_OAUTH_CLIENT_ID=votre_identifiant_client_google
GOOGLE_OAUTH_CLIENT_SECRET=votre_secret_client_google
GITHUB_OAUTH_CLIENT_ID=votre_identifiant_client_github
GITHUB_OAUTH_CLIENT_SECRET=votre_secret_client_github
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=votre_identifiant_client_pocketid
POCKETID_OAUTH_CLIENT_SECRET=votre_secret_client_pocketid
```

Consultez la page [Authentification OAuth](oauth-authentication.md) pour obtenir des instructions de configuration détaillées pour chaque fournisseur.

## Niveaux de journalisation

* `DJANGO_LOG_LEVEL` : niveau de journalisation pour Django et les bibliothèques internes ; la valeur par défaut est INFO
* `CM_LOG_LEVEL` : niveau de journalisation pour Cousins Matter ; la valeur par défaut est INFO

## Configuration réseau

* `ALLOWED_HOSTS` : liste d’hôtes séparés par des virgules. La valeur par défaut est « 127.0.0.1,localhost,<SITE_DOMAIN\> ». __Vous DEVEZ définir ALLOWED_HOSTS pour l’environnement de production__ et cette variable __DOIT__ contenir l’URL complète de votre site et, parfois, en fonction des paramètres réseau de votre hébergeur, l’adresse IP générale du site, par exemple :

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS` : liste d’hôtes séparés par des virgules. La valeur par défaut est vide.

	__ATTENTION !__ Si votre journal affiche des erreurs telles que

    `Forbidden (Échec de la vérification de l'origine - https://my.cousins-matter.com/ ne correspond à aucune origine de confiance.) : /members/login/`

    vous devez définir `CORS_ALLOWED_ORIGINS=<votre domaine complet>` (par ex. https://my.cousins-matter.com) dans le fichier `.env`,

    __N'utilisez pas la syntaxe Python indiquée dans le message d'erreur !__.

	Si vous disposez de plusieurs hôtes, énumérez-les séparés par des virgules, par exemple :

    `CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

    À titre d’information, `CSRF_TRUSTED_ORIGINS` prend la valeur de `CORS_ALLOWED_ORIGINS`

## Internationalisation

* `LANGUAGE_CODE` : par exemple « fr » ou « fr-CA ». La valeur par défaut est « en-US ».
* `TIME_ZONE` : fuseau horaire, la valeur par défaut est « Europe/Paris ».

## Propriétés de messagerie

* `EMAIL_HOST` : nom d’hôte SMTP, pas de valeur par défaut
* `EMAIL_PORT` : port de connexion au serveur SMTP
* `EMAIL_USE_TLS` : le serveur SMTP utilise STARTLS si la valeur est « true » ; la valeur par défaut est « true »
* `EMAIL_USE_SSL` : le serveur SMTP utilise SSL si la valeur est « true » ; la valeur par défaut est « false »
* `EMAIL_HOST_USER` : nom d’utilisateur pour se connecter au serveur SMTP.
* `EMAIL_HOST_PASSWORD` : mot de passe pour se connecter au serveur SMTP
* `DEFAULT_FROM_EMAIL` : adresse e-mail par défaut à utiliser lors de l'envoi d'e-mails

## Base de données

* `POSTGRES_USER` : l'utilisateur PostgreSQL ; la valeur par défaut est « cousinsmatter »
* `POSTGRES_PASSWORD` : mot de passe PostgreSQL. Il est généré automatiquement si vous utilisez manage_cousins_matter.py pour installer ou migrer Cousins Matter. __AVERTISSEMENT !__ N’utilisez que les caractères spéciaux -_./* si vous souhaitez le modifier. Évitez absolument les caractères : et @ !
* `POSTGRES_DB` : base de données PostgreSQL ; la valeur par défaut est « cousinsmatter »
* `POSTGRES_HOST` : l’hôte PostgreSQL ; la valeur par défaut est « postgres »

* `REDIS_HOST` : l’hôte Redis ; la valeur par défaut est « redis »

## Autres stockages multimédias

* `MEDIA_STORAGE` et `MEDIA_STORAGE_OPTIONS` : voir [Stockage multimédia](/media-storage.md)

## REMARQUES

__(*) AVERTISSEMENT :__ Si vous souhaitez modifier l’une des variables contrôlant la taille des fichiers pouvant être téléchargés et que vous utilisez le proxy inverse Nginx, veuillez vérifier que la valeur de `client_max_body_size` dans config/nginx/nginx.conf reste supérieure à la taille des variables que vous modifiez ci-dessus. Sinon, vous obtiendrez une erreur 413 de la part de Nginx. La valeur par défaut fournie est élevée (20 Mo), mais vous devrez peut-être l’augmenter pour prendre en charge des vidéos plus volumineuses.
