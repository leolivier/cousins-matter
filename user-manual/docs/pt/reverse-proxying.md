# Proxy inverso

## Proxy inverso com Nginx (predefinição)

Existe uma configuração predefinida de proxy inverso do Cousins Matter com Nginx. Está localizada no ficheiro config/nginx/nginx.conf.
Por predefinição, esta configuração é iniciada quando executa `docker compose up -d`.

Pode editar o ficheiro de configuração para o adaptar às suas necessidades.
Se não quiser que o nginx seja iniciado quando executa `docker compose up -d`, pode comentar o serviço nginx no ficheiro docker-compose.yml, mas precisará de outro proxy que sirva, pelo menos, os ficheiros estáticos e os média.

## Proxy inverso com Apache

Se não gosta do Nginx e prefere utilizar o Apache, também é fácil fazer um proxy inverso do Cousins Matter com o Apache. O seguinte ficheiro de configuração não foi testado, mas deverá funcionar sem problemas:

```
Define MyInternalURI ${MyInternalIP}:8000   #<-- indique aqui o endereço IP interno do seu servidor, adapte a porta se necessário
Define MyDomain cousins-matter.org           #<-- mude o domínio para o seu

# redirecionamento de http para https
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

Copie as linhas acima para /etc/apache2/sites-available/\<your domain>.conf

Depois, execute `sudo a2ensite <your domain>` para ativar o seu sítio e execute `sudo systemctl reload apache2` para que seja tido em conta pelo apache.

Agora, obtenha o seu certificado do Let's Encrypt utilizando o comando `certbot` (ver https://certbot.eff.org/ para a instalação):

```
domain=<your domain here>
sudo certbot --keep --expand --allow-sub set-of-names --cert-path /etc/letsencrypt/live/$domain --cert-name $domain -d $domain -d www.$domain --apache certonly
```

Isto deverá criar o certificado e instalá-lo no sítio certo.

Agora, já pode aceder ao seu domínio em https://\<your domain>

