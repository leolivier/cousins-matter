# Reverse proxy

## Reverse proxy con Nginx (predefinito)

Esiste una configurazione predefinita per fare il reverse proxy di Cousins Matter con Nginx. Si trova nel file config/nginx/nginx.conf.
Per impostazione predefinita, questa configurazione viene avviata quando esegui `docker compose up -d`.

Puoi modificare questo file di configurazione per adattarlo alle tue esigenze.
Se non vuoi che nginx venga avviato quando esegui `docker compose up -d`, puoi commentare il servizio nginx nel file docker-compose.yml, ma ti servirà un altro proxy almeno per servire i file statici e i media.

## Reverse proxy con Apache

Se non ti piace Nginx e preferisci usare Apache, è altrettanto facile fare il reverse proxy di Cousins Matter con Apache. Il seguente file di configurazione non è stato testato ma dovrebbe funzionare senza problemi:

```
Define MyInternalURI ${MyInternalIP}:8000   #<-- put here your internal server IP address, adapt the port if needed
Define MyDomain cousins-matter.org          #<-- change the domain to yours

# redirection from http to https
<VirtualHost *:80>
	ServerName ${MyDomain}
	ServerAlias www.${MyDomain}
	Redirect permanent / https://${MyDomain}/
</VirtualHost>

<VirtualHost *:443>
	ServerName ${MyDomain}
	ServerAlias ${MyDomain}
	# this assumes you have a Let's Encrypt certificate
	SSLCertificateFile /etc/letsencrypt/live/${MyDomain}/fullchain.pem    #<-- this is where letsencrypt usually stores the up-to-date certificates
	SSLCertificateKeyFile /etc/letsencrypt/live/${MyDomain}/privkey.pem   #<-- same for private key
	LogLevel error
	CustomLog /var/log/apache2/${MyDomain}-access.log combined
	ErrorLog /var/log/apache2/${MyDomain}-error.log

	DocumentRoot /none
	ProxyPreserveHost On
	ProxyRequests Of
	# no proxy for /static and /media
	ProxyPass "/static" !
	ProxyPass "/media" !
	# no proxy for letsencrypt challenges
	ProxyPass "/.well-known/acme-challenge" !
	ProxyPass "/" "http://${MyInternalURI}/"
	ProxyPassReverse "/"  "http://${MyInternalURI}/"
	ProxyPassReverseCookiePath "/" "/"
	ProxyPassReverseCookieDomain ${MyInternalURI} ${MyDomain}
	RequestHeader set X-Forwarded-Proto "https"

	# Redirect www to non-www
	RewriteEngine On
	RewriteCond %{HTTP_HOST} ^www\.(.*)$ [NC]
	RewriteRule ^(.*)$ https://%1/$1 [L,R=301]
</VirtualHost>
```

Copia le righe sopra in /etc/apache2/sites-available/\<your domain>.conf

Poi esegui `sudo a2ensite <your domain>` per attivare il tuo sito e lancia `sudo systemctl reload apache2` affinché venga preso in carico da apache.

Ora ottieni il tuo certificato da Let's Encrypt con il comando `certbot` (vedi https://certbot.eff.org/ per l'installazione):

```
domain=<your domain here>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

Questo dovrebbe creare il certificato e installarlo nel posto giusto.

Ora puoi accedere al tuo dominio all'indirizzo https://\<your domain>
