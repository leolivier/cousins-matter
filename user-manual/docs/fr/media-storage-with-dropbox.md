# AVERTISSEMENT ⚠️ ACTUELLEMENT, SEUL S3 EST PRIS EN CHARGE ; DROPBOX NE FONCTIONNE PAS (probablement en raison d'un problème avec django-storages)


# Stockage des médias

## AVERTISSEMENTS

* __Il s'agit actuellement d'une <span class="blinking-text"><u>fonctionnalité BETA</u></span> !__
* __Ces paramètres sont plus complexes et sont <u>réservés aux utilisateurs avancés</u>.__

## Stockage par défaut des médias
Par défaut, les médias sont stockés dans le sous-répertoire « media » du même système de fichiers que Cousins Matter.

C’est très simple, mais cela présente certains inconvénients, notamment en matière de sécurité, comme expliqué dans [cet article](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Autres stockages multimédias

Cousins Matter prend également en charge toute une série d’autres stockages multimédias grâce au package « django-storages ». Pour configurer un tel stockage, il vous suffit de définir deux nouvelles variables dans votre fichier .env : MEDIA_STORAGE et MEDIA_STORAGE_OPTIONS.

Les espaces de stockage multimédia pris en charge par django-storages au moment de la rédaction de cette page sont les suivants :

* Amazon S3
* Apache Libcloud
* Azure Storage
* Dropbox
* FTP
* Google Cloud Storage
* SFTP
* Compatibles S3
    * Backblaze B2
    * Cloudflare R2
    * Digital Ocean
    * Oracle Cloud
    * Scaleway

**À ce jour, seuls les espaces de stockage Dropbox et Cloudflare R2 ont été testés et expérimentés**, mais tous les autres espaces devraient fonctionner à condition de trouver la bonne configuration. Consultez les sections [Autres espaces de stockage compatibles S3](#other-s3-compatible-storages) et [Espaces de stockage non testés](#non-tested-storages) ci-dessous.

Si vous parvenez à mettre en place une configuration fonctionnelle pour des espaces de stockage non testés, veuillez créer une Pull Request sur GitHub pour ce fichier afin d’expliquer comment cela fonctionne.

### Cloudflare R2

Pour utiliser Cloudflare R2, vous devez bien sûr commencer par [créer un compte sur Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Ensuite, vous devez [créer un compartiment S3 sur Cloudflare R2 – onglet « Dashboard »](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Notez bien le nom du compartiment.

Vous devez également [créer un jeton d’application](https://developers.cloudflare.com/r2/api/tokens/). Notez bien la clé d’accès, la clé secrète et les URL des points de terminaison qui s’affichent sur la dernière page lors de la création de votre jeton API.

Une fois ces étapes effectuées, la configuration dans votre fichier .env devrait ressembler à ceci :
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS=“{« access_key »:« <votre clé d'accès> »,« secret_key »:« <votre clé secrète> »,« bucket_name »:« <le nom de votre bucket> »,“endpoint_url”:« https://<votre identifiant de compte>.r2.cloudflarestorage.com »}”
```
Redémarrez ensuite Cousins Matter : `docker compose restart cousins-matter`

#### Autres stockages compatibles S3

La configuration pour d’autres stockages compatibles S3 (y compris AWS S3, le stockage d’origine) devrait être similaire à celle de R2, mais n’a pas encore été testée.
Comme tous ces backends partagent la même implémentation, vous n’avez pas besoin de créer votre propre image comme décrit pour les [stockages non testés](#non-tested-storages) ci-dessous.
Consultez la [documentation de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) pour savoir quelles variables spécifiques doivent être définies dans les options pour votre cas particulier.

### Dropbox

Vous devez disposer d’un compte Dropbox pour utiliser ce stockage (voir https://www.dropbox.com/register).
Ensuite, vous devrez [créer une application](https://www.dropbox.com/developers/apps). Le formulaire de paramètres devrait ressembler à ceci :
![créer une application Dropbox](assets/create_dropbox_app.webp). Notez bien la clé de l’application et le secret de l’application.
Rendez-vous dans l’onglet « Autorisations » et remplissez le formulaire comme suit :
![autorisations de l’application Dropbox](assets/dropbox_app_permissions.webp)
N’oubliez pas de cliquer sur « Soumettre » à la fin…

Ensuite, comme décrit sur la [page Dropbox de Django-storages](https://django-storages.readthedocs.io/en/latest/backends/dropbox.html), récupérez votre code d’autorisation, puis, à l’aide de ce code, obtenez l’access_token (commençant par « sl. ») et le refresh token.

Une fois cette étape terminée, la configuration dans votre fichier .env devrait ressembler à ceci :

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS=“{« app_key »:« <votre clé d'application> »,« app_secret »:« <votre secret d'application> »,« root_path »:« / »,« oauth2_access_token »:« <votre jeton d'accès> »,“oauth2_refresh_token”:« <votre jeton de rafraîchissement> »}”
```

## Stockages non testés

### Installer le module Python nécessaire

**Remarque :** cela n’est pas nécessaire pour tous les backends compatibles S3, voir ci-dessus [Autres stockages compatibles S3](#other-s3-compatible-storages)

Vous devez d’abord installer un module Python spécifique qui implémente la connexion à votre backend.

Consultez la page dédiée à votre backend dans la [documentation de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) pour connaître le nom de votre paquet, qui devrait se présenter sous la forme `pip install django-storages[<nom du backend>]`. Notez bien la valeur de `<nom du backend>`, vous devrez l’utiliser pour la remplacer ci-dessous.

Il existe deux façons d’installer ce paquet, utilisez la méthode qui vous convient le mieux…

* Soit vous créez votre propre image de Cousins Matter à partir de l’image officielle, comme suit :
    1. Créez un fichier Dockerfile de cette manière :

        ```
        FROM ghcr.io/leolivier/cousins-matter:latest
        RUN pip install django-storages[<backend name>]
        ```

1. Créez la nouvelle image (modifiez le nom de l'image à votre guise) :

       ```
       docker build -t cousins-matter:local .
       ```

	1. Définissez COUSINS_MATTER_IMAGE dans votre fichier .env pour qu'il pointe vers `cousins-matter:local` (ou vers votre balise si vous l'avez modifiée)
   1. Recréez les conteneurs

       ```
       docker compose up -d --force-recreate cousins-matter qcluster
       ```

	Vous devrez reconstruire l’image et recréer les conteneurs à chaque fois qu’une nouvelle version est mise à disposition.

* Vous pouvez également mettre à jour les conteneurs en cours d’exécution comme suit :

   ```
   docker exec -it cousins-matter pip install django-storages[<nom du backend>]
   docker exec -it cousins-matter.qcluster pip install django-storages[<nom du backend>]
   ```

	Vous devrez exécuter ces deux commandes chaque fois que vos conteneurs seront mis à jour avec une nouvelle image officielle.

__AVERTISSEMENT__ : dans certains cas, il y a plusieurs paquets à installer. Par exemple, si vous utilisez Azure Storage avec Managed Identity, vous devrez installer un autre paquet pour Managed Identity. Procédez comme décrit ci-dessus et ajoutez simplement les noms des autres paquets à la fin de la ligne de commande `pip install`.

### Créer la configuration

Consultez les configurations ci-dessus pour [Dropbox](#dropbox) et [Cloudflare R2](#cloudflare-r2) afin de comprendre le fonctionnement des deux variables MEDIA_STORAGE et MEDIA_STORAGE_OPTIONS, et consultez la [documentation de django-storages](https://django-storages. readthedocs.io/en/latest/index.html) de votre backend pour adapter ces configurations à votre cas particulier.

MEDIA_STORAGE doit être récupérée sur la page de votre backend. Utilisez la valeur de BACKEND dans le bloc STORAGES (par exemple, storages.backends.azure_storage.AzureStorage pour le backend Azure Storage).

MEDIA_STORAGE_OPTIONS doit figurer sur une seule ligne. Il doit respecter le format suivant (l’ordre des guillemets simples et doubles est important !)

```
MEDIA_STORAGE_OPTIONS=“{« option1 »:« value1 »,“option2”:« value2 »,...}”
```

Remplacez option1 et option2 par les variables en minuscules décrites dans la documentation et leurs valeurs adaptées à votre cas.

## Migration du répertoire media vers un stockage externe

__ASTUCE__ : si vous avez déjà enregistré de nombreux fichiers dans votre répertoire « media », l’utilisation de [rclone](https://rclone.org/install/) vous fera gagner du temps pour migrer vos fichiers vers votre nouveau backend. Commencez par créer une configuration pour votre backend (`rclone config`), puis copiez vos fichiers multimédias : `rclone copy ./media <votre backend>:<votre répertoire racine>`
