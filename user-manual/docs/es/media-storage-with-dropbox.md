# ADVERTENCIA ⚠️ ACTUALMENTE SOLO S3 ESTÁ SOPORTADO, DROPBOX NO FUNCIONA (probablemente debido a un problema con django-storages)


# Almacenamiento de los medios

## ADVERTENCIAS

* __¡Esto es actualmente una función en fase <span class="blinking-text"><u>BETA</u></span>!__
* __Estos ajustes son más complejos y están <u>reservados a usuarios avanzados</u>.__

## Almacenamiento de medios por defecto
Por defecto, los medios se almacenan en el subdirectorio 'media', en el mismo sistema de archivos que Cousins Matter.

Esto es muy sencillo, pero tiene algunos inconvenientes, especialmente en el aspecto de la seguridad, tal como se explica en [este artículo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Otros almacenamientos de medios

Cousins Matter también admite una serie de otros almacenamientos de medios mediante el paquete 'django-storages'. Para configurar dicho almacenamiento, solo necesitas definir dos nuevas variables en tu archivo .env: MEDIA_STORAGE y MEDIA_STORAGE_OPTIONS.

Los almacenamientos de medios soportados por django-storages en el momento de escribir esta página son:

* Amazon S3
* Apache Libcloud
* Azure Storage
* Dropbox
* FTP
* Google Cloud Storage
* SFTP
* Compatibles con S3
	* Backblaze B2
	* Cloudflare R2
	* Digital Ocean
	* Oracle Cloud
	* Scaleway

**Solo el almacenamiento Dropbox y el almacenamiento Cloudflare R2 han sido probados y experimentados hasta ahora**, pero todos los demás almacenamientos deberían funcionar mientras encuentres la configuración adecuada. Consulta [Otros almacenamientos compatibles con S3](#other-s3-compatible-storages) y [Almacenamientos no probados](#non-tested-storages) más abajo.

Si consigues crear una configuración funcional para almacenamientos no probados, por favor crea un Pull Request en GitHub sobre este archivo para explicar cómo funciona.

### Cloudflare R2

Para utilizar Cloudflare R2, obviamente primero necesitas [crear una cuenta en Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Luego, debes [crear un bucket S3 en Cloudflare R2 - pestaña Dashboard](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Recuerda el nombre del bucket.

También necesitas [crear un token de aplicación](https://developers.cloudflare.com/r2/api/tokens/). Recuerda la clave de acceso, la clave secreta y las URL de endpoint en la última página, cuando se cree tu token de API.

Una vez hecho esto, la configuración en tu archivo .env debería quedar así:
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS='{"access_key":"<your access key>","secret_key":"<your secret key>","bucket_name":"<your bucket name>","endpoint_url":"https://<your account id>.r2.cloudflarestorage.com"}'
```

Luego reinicia Cousins Matter: `docker compose restart cousins-matter`

#### Otros almacenamientos compatibles con S3

La configuración de otros almacenamientos compatibles con S3 (incluido AWS S3, el original) debería ser parecida a la de R2, pero aún no se ha probado.
Como todos estos backends comparten la misma implementación, no necesitas crear tu propia imagen como se describe para los [almacenamientos no probados](#non-tested-storages) más abajo.
Echa un vistazo a la [documentación de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para ver qué variables específicas debes definir en las opciones para tu caso concreto.

### Dropbox

Necesitarás tener una cuenta de Dropbox para utilizar este almacenamiento (ver https://www.dropbox.com/register).
Luego, tendrás que [crear una aplicación](https://www.dropbox.com/developers/apps). El formulario de Settings debería quedar así:
![creación de la aplicación dropbox](assets/create_dropbox_app.webp). Recuerda la app key y la app secret.
Ve a la pestaña Permissions y rellena el formulario así:
![permisos de la aplicación dropbox](assets/dropbox_app_permissions.webp)
No olvides hacer clic en Submit al final...

Luego, tal como se describe en la [página de Dropbox de Django-storages](https://django-storages.readthedocs.io/en/latest/backends/dropbox.html), obtén tu código de autorización y, con este código, consigue el access_token (que empieza por "sl.") y el refresh token.

Una vez hecho esto, la configuración en tu archivo .env debería quedar así:

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS='{"app_key":"<your app key>","app_secret":"<your app secret>","root_path":"/","oauth2_access_token":"<your access token>","oauth2_refresh_token":"<your refresh token>"}'
```

## Almacenamientos no probados

### Instalar el paquete de Python necesario

**Nota:** Esto no es necesario para todos los backends compatibles con S3, consulta más arriba [Otros almacenamientos compatibles con S3](#other-s3-compatible-storages)

Primero, necesitas instalar un paquete de python específico que implemente el enlace con tu backend.

Consulta la página relacionada con tu backend en la [documentación de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para ver el nombre de tu paquete, que debería aparecer como `pip install django-storages[<backend name>]`. Recuerda el valor de `<backend name>`, lo utilizarás para sustituirlo más abajo.

Hay dos formas de instalar este paquete; utiliza la que mejor te convenga...

* O bien creas tu propia imagen de Cousins Matter derivada de la oficial, así:
	1. crea un Dockerfile de esta manera:

		```
		FROM ghcr.io/leolivier/cousins-matter:latest
		RUN pip install django-storages[<backend name>]
		```

	1. construye la nueva imagen (cambia la etiqueta de la imagen como quieras):

		```
		docker build -t cousins-matter:local .
		```

	1. define COUSINS_MATTER_IMAGE en tu archivo .env para que apunte a `cousins-matter:local` (o a tu etiqueta si la has cambiado)
	1. vuelve a crear los contenedores

		```
		docker compose up -d --force-recreate cousins-matter qcluster
		```

	Tendrás que reconstruir la imagen y volver a crear los contenedores cada vez que se entregue una nueva versión.

* O bien actualizas los contenedores en ejecución así:

	```
	docker exec -it cousins-matter pip install django-storages[<backend name>]
	docker exec -it cousins-matter.qcluster pip install django-storages[<backend name>]
	```

	Tendrás que ejecutar estos 2 comandos cada vez que tus contenedores se actualicen con una nueva imagen oficial.

__ADVERTENCIA__: en algunos casos, hay más de un paquete que instalar. Por ejemplo, si utilizas Azure Storage con Managed Identity, necesitarás instalar otro paquete para Managed Identity. Procede como se ha descrito anteriormente y simplemente añade los nombres de los demás paquetes al final de la línea de comandos `pip install`

### Crear la configuración

Echa un vistazo a las configuraciones anteriores de [Dropbox](#dropbox) y [Cloudflare R2](#cloudflare-r2) para entender cómo funcionan las 2 variables MEDIA_STORAGE y MEDIA_STORAGE_OPTIONS, y consulta la [documentación de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) de tu backend para adaptar estas configuraciones a tu caso.

MEDIA_STORAGE debe tomarse de la página de tu backend. Utiliza el valor de BACKEND en el bloque STORAGES (por ejemplo, storages.backends.azure_storage.AzureStorage para el backend Azure Storage).

MEDIA_STORAGE_OPTIONS debe permanecer en una sola línea. Tiene el siguiente formato (¡el orden de las comillas simples y dobles es importante!)

```
MEDIA_STORAGE_OPTIONS='{"option1":"value1","option2":"value2",...}'
```

Sustituye option1, option2 por las variables en minúsculas descritas en la documentación y sus valores para tu caso.

## Migración del directorio media a un almacenamiento externo

__CONSEJO__: si ya has guardado muchos archivos en tu directorio media, usar [rclone](https://rclone.org/install/) te ahorrará tiempo al migrar tus archivos a tu nuevo backend. Primero crea una configuración para tu backend (`rclone config`) y luego copia tus archivos de medios: `rclone copy ./media <your backend>:<your root>`
