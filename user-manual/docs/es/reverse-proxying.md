# Proxy inverso

## Proxy inverso con Nginx (por defecto)

Existe una configuración por defecto para poner Cousins Matter detrás de un proxy inverso con Nginx. Se encuentra en el archivo config/nginx/nginx.conf.
Por defecto, esta configuración se inicia cuando ejecutas `docker compose up -d`.

Puedes editar este archivo de configuración para adaptarlo a tus necesidades.
Si no quieres que nginx se inicie cuando ejecutas `docker compose up -d`, puedes comentar el servicio nginx en el archivo docker-compose.yml, pero necesitarás otro proxy al menos para servir los archivos estáticos y los medios.

## Proxy inverso con Apache

Si no te gusta Nginx y prefieres utilizar Apache, también es fácil poner Cousins Matter detrás de un proxy inverso con Apache. El siguiente archivo de configuración no se ha probado, pero debería funcionar sin problemas:

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

Copia las líneas anteriores a /etc/apache2/sites-available/\<tu dominio>.conf

Luego, ejecuta `sudo a2ensite <tu dominio>` para activar tu sitio y ejecuta `sudo systemctl reload apache2` para que apache lo tenga en cuenta.

Ahora, obtén tu certificado de Let's Encrypt utilizando el comando `certbot` (ver https://certbot.eff.org/ para la instalación):

```
domain=<your domain here>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

Esto debería crear el certificado e instalarlo en el lugar adecuado.

Ahora ya puedes acceder a tu dominio en https://\<tu dominio>
