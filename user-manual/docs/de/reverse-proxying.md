# Reverse Proxy

## Reverse Proxy mit Nginx (Standard)

Es gibt eine Standardkonfiguration, um Cousins Matter mit Nginx als Reverse Proxy zu betreiben. Sie befindet sich in der Datei config/nginx/nginx.conf.
Standardmäßig wird diese Konfiguration gestartet, wenn Sie `docker compose up -d` ausführen.

Sie können diese Konfigurationsdatei bearbeiten, um sie an Ihre Bedürfnisse anzupassen.
Wenn Sie nicht möchten, dass nginx beim Ausführen von `docker compose up -d` gestartet wird, können Sie den nginx-Dienst in der Datei docker-compose.yml auskommentieren; Sie benötigen dann aber einen anderen Proxy, der zumindest die statischen Dateien und die Mediendateien ausliefert.

## Reverse Proxy mit Apache

Wenn Sie Nginx nicht mögen und stattdessen Apache bevorzugen, ist es auch einfach, Cousins Matter mit Apache als Reverse Proxy zu betreiben. Die folgende Konfigurationsdatei wurde nicht getestet, sollte aber problemlos funktionieren:

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

Kopieren Sie die obigen Zeilen nach /etc/apache2/sites-available/\<your domain>.conf

Führen Sie dann `sudo a2ensite <your domain>` aus, um Ihre Website zu aktivieren, und `sudo systemctl reload apache2`, damit sie von Apache berücksichtigt wird.

Holen Sie sich nun Ihr Zertifikat von Let's Encrypt mit dem Befehl `certbot` (siehe https://certbot.eff.org/ zur Installation):

```
domain=<your domain here>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

Damit sollte das Zertifikat erstellt und am richtigen Ort installiert werden.

Jetzt können Sie auf Ihre Domain unter https://\<your domain> zugreifen
