## Reverse proxying with Apache
It is easy to reverse proxy Cousins Matter with Apache. The following config file has been tested and should work seamlessly:
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
  SSLCertificateFile /etc/letsencrypt/live/${MyDomain}/fullchain.pem    #<-- this is where letsencrypt usually stores the up-to-date certificates
  SSLCertificateKeyFile /etc/letsencrypt/live/${MyDomain}/privkey.pem   #<-- same for private key
# LogLevel debug
  LogLevel error
  CustomLog /var/log/apache2/${MyDomain}-access.log combined
  ErrorLog /var/log/apache2/${MyDomain}-error.log

  DocumentRoot /none
  ProxyPreserveHost On
  ProxyRequests Of
# No proxy letsencrypt challenges
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

## Reverse proxying with Nginx
This configuration file for Nginx is the exact equivalent of above Apache configuration (or at least it should be but it was not tested):
```
# Variables definition
set $my_domain "cousins-matter.org";  # <-- Change this to your domain
map $host $domain {
    default $my_domain;
}
upstream backend {
    server INTERNAL_IP:8000;   # <-- Replace INTERNAL_IP with your internal server IP address
}

# HTTP to HTTPS redirection
server {
    listen 80;
    server_name $my_domain www.$my_domain;
    return 301 https://$my_domain$request_uri;
}

# Main HTTPS configuration
server {
    listen 443 ssl;
    server_name $my_domain www.$my_domain;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/$my_domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$my_domain/privkey.pem;
    
    # Logs configuration
    error_log /var/log/nginx/$my_domain-error.log error;
    access_log /var/log/nginx/$my_domain-access.log combined;
    
    # Redirect www to non-www
    if ($host ~* ^www\.(.*)) {
        return 301 https://$1$request_uri;
    }
    
    # Let's Encrypt challenges handling
    location /.well-known/acme-challenge {
        root /var/www/html;
    }
    
    # Proxy configuration
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        
        # Cookies handling
        proxy_cookie_path / "/";
        proxy_cookie_domain backend $domain;
        
        # Additional proxy settings
        proxy_redirect off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
