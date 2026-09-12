# Almacenamiento de los medios

## ADVERTENCIAS

* __¡Esto es actualmente una función en fase <span class="blinking-text"><u>BETA</u></span>!__
* __Estos ajustes son más complejos y están <u>reservados a usuarios avanzados</u>.__

## Almacenamiento de medios por defecto

Por defecto, los medios se almacenan en el subdirectorio 'media', en el mismo sistema de archivos que Cousins Matter.

Esto es muy sencillo, pero tiene algunos inconvenientes, especialmente en el aspecto de la seguridad, tal como se explica en [este artículo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Otros almacenamientos de medios

Cousins Matter también admite almacenamientos de medios S3 mediante el paquete 'django-storages'. Para configurar dicho almacenamiento, solo necesitas definir dos nuevas variables en tu archivo .env: MEDIA_STORAGE y MEDIA_STORAGE_OPTIONS.

**Solo el almacenamiento Cloudflare R2 ha sido probado y experimentado hasta ahora**, pero otros almacenamientos S3 deberían funcionar mientras encuentres la configuración adecuada. Consulta [Otros almacenamientos compatibles con S3](#other-s3-compatible-storages) más abajo.

Si consigues crear una configuración funcional para almacenamientos no probados, por favor crea un Pull Request en GitHub sobre esta página para explicar cómo funciona.

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

Echa un vistazo a la [documentación de django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para ver qué variables específicas debes definir en las opciones para tu caso concreto.


## Migración del directorio media a un almacenamiento S3 externo

Puedes usar las herramientas del almacenamiento S3 para ello. Por ejemplo, en AWS S3, puedes usar

```
$ aws s3 sync ./media s3://YOUR_BUCKET/media/
```

__CONSEJO__: Sea cual sea tu proveedor S3, usar [rclone](https://rclone.org/install/) te ahorrará tiempo al migrar tus archivos a tu nuevo backend. Primero crea una configuración para tu backend (`rclone config`) y luego copia tus archivos de medios: `rclone copy ./media <your backend>:<your root>`
