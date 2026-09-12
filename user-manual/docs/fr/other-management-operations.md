# Autres opérations de gestion

## Mise à jour de Cousins Matter
### En production
Récupérez la dernière image et redémarrez le conteneur
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Reconstruire l'image à partir du code source
Découvrez comment compiler à partir du code source pour la première fois [ici](installation.md#compiler-a-partir-du-code-source).
Pour mettre à jour votre image à partir du code source, procédez simplement comme suit :
```
git pull        # actualiser les sources
uv sync         # synchroniser les dépendances
make build      # compiler l’image
make up         # redémarrer les services (cela recompile l’image avant le redémarrage)
# alternative à la dernière ligne :
make up4run     # redémarrer les autres services, sauf Cousins Matter
make run        # démarrer uniquement Cousins Matter en dehors de Docker (utile pour le débogage)
```

## Renouveler votre clé secrète
De temps en temps (par exemple une fois par mois), vous devriez renouveler la clé secrète de Cousins Matter. Pour ce faire, exécutez la commande suivante :

```
./manage_cousins_matter.sh rotate-secrets
```

Cette commande changera la clé secrète et mettra à jour les PREVIOUS_SECRET_KEYS dans le fichier .env.

Comme Cousins Matter ne peut pas modifier lui-même sa clé secrète, vous devrez redémarrer les conteneurs Cousins Matter pour appliquer la nouvelle clé secrète.

Pour ce faire, exécutez la commande suivante :

```
docker compose up -d --force-recreate
```
