# Reverse Proxying

## Reverse proxying with Nginx (default)

There is a default configuration to reverse proxy Cousins Matter with Nginx. It is located in the config/nginx.conf file.
By default, this configuration is started when you run `docker compose up -d`.

You can edit this configuration file to adapt it to your needs.
If you don't want nginx to be started when you run `docker compose up -d`, you can comment the nginx service from the docker-compose.yml file but you will need another proxy at least to serve the static and the media files.

## Reverse proxying with Apache

If you don't like Nginx and prefer to use Apache, it is also easy to reverse proxy Cousins Matter with Apache. The following config file has not been tested but should work seamlessly:

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

Copy the lines above to /etc/apache2/sites-available/\<your domain>.conf

Then, execute `sudo a2ensite <your domain>` to enable your site and run `sudo systemctl reload apache2` so that it is taken into account by apache.

Now, get your certificate from Let's Encrypt using the `certbot` command (see https://certbot.eff.org/ for install):

```
domain=<your domain here>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

This should create the certificate and install it at the right place.

Now, you can now access your domain to https://\<your domain>

