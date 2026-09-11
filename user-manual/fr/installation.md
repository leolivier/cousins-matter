# Installation de Cousins Matter

Cette installation a été testée sous Linux et Windows+WSL2 avec Ubuntu ou Debian + Docker Desktop. (Le script d'installation n'a pas encore été testé sous macOS, mais devrait fonctionner avec très peu de modifications)

## Installation en production

### Prérequis

Si ce n'est pas déjà fait, installez Docker sur votre serveur :
```
curl https://get.docker.com | sh
```

Vous aurez également besoin d’un environnement Python 3.14+ pour exécuter le script d’administration de Cousins Matter.

### Télécharger et exécuter le script d’administration de Cousins Matter

Veuillez remplacer dans le lien ci-dessous le paramètre **<release\>** par la version actuelle de Cousins Matter :
![Version GitHub](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<version>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <répertoire>] [-r <version>]
```

* si l'option -d répertoire n'est pas spécifiée, l'installation s'effectuera dans le répertoire courant
* si l'option -r version n'est pas spécifiée, la dernière version sera installée

Cette commande va :

* télécharger les fichiers nécessaires à Cousins Matter ;
* créer les répertoires nécessaires ;
* créer le fichier .env de base à partir d'un exemple ;
* ouvrir le fichier .env dans un éditeur pour que vous puissiez l'adapter à vos besoins (voir la page [Paramètres](settings.md)). En particulier, __n’oubliez pas d’ajouter les informations nécessaires à la création du superutilisateur__.

Ce script peut également vous aider à [migrer de la version v1 à la version v2 de Cousins Matter](migrate-from-v1-to-v2.md) et à [renouveler votre clé secrète de temps à autre](other-management-operations.md#rotate-your-secret-key).

Pour afficher les différentes commandes disponibles, exécutez :

```
python manage_cousins_matter.py -h
```

Pour obtenir de l’aide sur une commande spécifique, exécutez :
```
python manage_cousins_matter.py <commande> -h
```

### Démarrer Cousins Matter

```
cd <répertoire>
docker compose up -d
```

__La première fois__, rendez-vous sur http://127.0.0.1:8000/members/profile, connectez-vous à l’aide du compte administrateur que vous venez de créer et complétez votre profil.

**Et voilà, c’est terminé !**

## Compiler à partir du code source

* Installez Docker et uv si ce n’est pas déjà fait

    ```
    curl https://get.docker.com | sh
  pip install uv
    ```

* Clonez le dépôt Git :

    ```
    git clone https://github.com/leolivier/cousins-matter.git
    cd cousins-matter
    ```

**Remarque à l’attention des contributeurs :** si vous souhaitez contribuer au développement de cousins-matter, commencez par créer un fork du projet sur GitHub, puis clonez votre propre dépôt.

* Créez et synchronisez votre environnement virtuel Python :
  ```
  uv sync
    ```

* Mettez à jour vos paramètres :
    Copiez `.env.example` dans `.env` et modifiez `.env` pour définir les propriétés en fonction de vos besoins ; consultez la page [Paramètres](settings.md).

    Vous pouvez créer automatiquement la clé SECRET_KEY en exécutant la commande suivante :

    ```
    ./manage_cousins_matter.sh rotate-secrets
    ```

* Compilez l’image Docker :

    ```
    make build t=cousins-matter:local
    ```

* Utilisez votre image locale en ajoutant la ligne suivante au fichier .env :
    ```
    COUSINS_MATTER_IMAGE=cousins-matter:local
    ```

* Démarrez le tout :

    ```
    make up
    ```

### Exécuter en dehors de Docker

Si vous souhaitez déboguer votre installation, vous pouvez l'exécuter en dehors de Docker.

Pour cela, au lieu de lancer `make up`, utilisez :
```
make up4run  # lancera les conteneurs nécessaires : postgres, redis et qcluster (en utilisant l'image construite précédemment)
# pour démarrer cousins-matter en mode développement
make run  # se rechargera automatiquement après chaque modification du code
# pour exécuter les tests (pas les tests d'interface utilisateur)
make test [t=<nom du test>]
# pour exécuter les tests d'interface utilisateur
make test-ui [t=<nom du test>]
# pour obtenir toutes les autres commandes make, il suffit d'exécuter
make
```
ou lancez le débogage depuis votre IDE (le projet est déjà configuré pour Visual Studio Code dans le fichier .vscode/launch.json)
