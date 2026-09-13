# Proxy inverse

## Proxy inverse avec Nginx (par défaut)

Il existe une configuration par défaut permettant de mettre en place un proxy inverse pour Cousins Matter avec Nginx. Elle se trouve dans le fichier config/nginx/nginx.conf.
Par défaut, cette configuration est lancée lorsque vous exécutez la commande `docker compose up -d`.

Vous pouvez modifier ce fichier de configuration pour l'adapter à vos besoins.
Si vous ne souhaitez pas que Nginx soit lancé lorsque vous exécutez la commande `docker compose up -d`, vous pouvez commenter le service Nginx dans le fichier docker-compose.yml, mais vous aurez alors besoin d’un autre proxy, au moins pour servir les fichiers statiques et multimédias.

## Proxy inverse avec Apache

Si vous n’appréciez pas Nginx et préférez utiliser Apache, il est également facile de mettre en place un proxy inverse pour Cousins Matter avec Apache. Le fichier de configuration suivant n’a pas été testé mais devrait fonctionner sans problème :

```
Define MyInternalURI ${MyInternalIP}:8000   #<-- indiquez ici l’adresse IP interne de votre serveur, adaptez le port si nécessaire
Define MyDomain cousins-matter.org          #<-- remplacez le domaine par le vôtre

# redirection de http vers https
<VirtualHost *:80>
    ServerName ${MyDomain}
    ServerAlias www.${MyDomain}
    Redirect permanent / https://${MyDomain}/
</VirtualHost>

<VirtualHost *:443>
    ServerName ${MyDomain}
    ServerAlias ${MyDomain}
    # ceci suppose que vous disposiez d’un certificat Let’s Encrypt
    SSLCertificateFile /etc/letsencrypt/live/${MyDomain}/fullchain.pem    #<-- c’est là que Let’s Encrypt stocke généralement les certificats à jour
	SSLCertificateKeyFile /etc/letsencrypt/live/${MyDomain}/privkey.pem   #<-- idem pour la clé privée
    LogLevel error
    CustomLog /var/log/apache2/${MyDomain}-access.log combined
    ErrorLog /var/log/apache2/${MyDomain}-error.log

    DocumentRoot /none
	ProxyPreserveHost On
    ProxyRequests Of
    # pas de proxy pour /static et /media
    ProxyPass « /static » !
    ProxyPass « /media » !
    # pas de proxy pour les défis Let's Encrypt
    ProxyPass « /.well-known/acme-challenge » !
    ProxyPass « / » « http://${MyInternalURI}/ »
	ProxyPassReverse « / »  « http://${MyInternalURI}/ »
    ProxyPassReverseCookiePath « / » « / »
    ProxyPassReverseCookieDomain ${MyInternalURI} ${MyDomain}
    RequestHeader set X-Forwarded-Proto « https »

    # Rediriger www vers non-www
	RewriteEngine On
    RewriteCond %{HTTP_HOST} ^www\.(.*)$ [NC]
    RewriteRule ^(.*)$ https://%1/$1 [L,R=301]
</VirtualHost>
```

Copiez les lignes ci-dessus dans /etc/apache2/sites-available/\<votre domaine>.conf

Ensuite, exécutez `sudo a2ensite <votre domaine>` pour activer votre site, puis `sudo systemctl reload apache2` afin qu’Apache en tienne compte.

Maintenant, obtenez votre certificat auprès de Let’s Encrypt à l’aide de la commande `certbot` (voir https://certbot.eff.org/ pour l’installation) :

```
domain=<votre domaine ici>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

Cela devrait créer le certificat et l'installer au bon emplacement.

Vous pouvez désormais accéder à votre domaine à l'adresse https://\<votre domaine>
