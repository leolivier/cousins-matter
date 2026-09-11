# Stockage des médias

## AVERTISSEMENTS

* __Il s'agit actuellement d'une <span class="blinking-text"><u>fonctionnalité BETA</u></span> !__
* __Ces paramètres sont plus complexes et sont <u>réservés aux utilisateurs avancés</u>.__

## Stockage par défaut des médias

Par défaut, les médias sont stockés dans le sous-répertoire « media », sur le même système de fichiers que Cousins Matter.

C’est très simple, mais cela présente certains inconvénients, notamment en matière de sécurité, comme expliqué dans [cet article](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Autres stockages multimédias

Cousins Matter prend également en charge les stockages multimédias S3 grâce au package « django-storages ». Pour configurer un tel stockage, il vous suffit de définir deux nouvelles variables dans votre fichier .env : MEDIA_STORAGE et MEDIA_STORAGE_OPTIONS.

**À ce jour, seul le stockage Cloudflare R2 a été testé et éprouvé**, mais d’autres stockages S3 devraient fonctionner à condition de trouver la bonne configuration. Consultez la section [Autres stockages compatibles S3](#other-s3-compatible-storages) ci-dessous.

Si vous parvenez à mettre en place une configuration fonctionnelle pour des stockages non testés, veuillez créer une Pull Request sur GitHub depuis cette page pour expliquer comment cela fonctionne.

### Cloudflare R2

Pour utiliser Cloudflare R2, vous devez bien sûr commencer par [créer un compte sur Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Ensuite, vous devez [créer un compartiment S3 sur Cloudflare R2 – onglet « Dashboard »](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Notez bien le nom du compartiment.

Vous devez également [créer un jeton d’application](https://developers.cloudflare.com/r2/api/tokens/). Notez bien la clé d’accès, la clé secrète et les URL des points de terminaison qui s’affichent sur la dernière page lors de la création de votre jeton API.

Une fois ces étapes effectuées, la configuration dans votre fichier .env devrait ressembler à ceci :

```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS=“{« access_key »:« <votre clé d'accès> »,« secret_key »:« <votre clé secrète> »,« bucket_name »:« <le nom de votre compartiment> »,“endpoint_url”:« https://<votre identifiant de compte>.r2.cloudflarestorage.com »}”
```

Redémarrez ensuite Cousins Matter : `docker compose restart cousins-matter`

#### Autres stockages compatibles S3

La configuration pour d’autres stockages compatibles S3 (y compris AWS S3, le stockage d’origine) devrait être similaire à celle de R2, mais elle n’a pas encore été testée.

Consultez la [documentation de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) pour savoir quelles variables spécifiques doivent être définies dans les options en fonction de votre cas particulier.


## Migration du répertoire « media » vers un stockage S3 externe

Vous pouvez utiliser les outils de gestion du stockage S3 à cette fin. Par exemple, sur AWS S3, vous pouvez utiliser :

```
$ aws s3 sync ./media s3://VOTRE_BUCKET/media/
```

__ASTUCE__ : Quel que soit votre fournisseur S3, l’utilisation de [rclone](https://rclone.org/install/) vous fera gagner du temps pour migrer vos fichiers vers votre nouveau backend. Créez d’abord une configuration pour votre backend (`rclone config`), puis copiez vos fichiers multimédias : `rclone copy ./media <votre backend>:<votre répertoire racine>`
