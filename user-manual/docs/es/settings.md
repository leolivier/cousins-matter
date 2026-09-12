# Ajustes

## Introducción

Los ajustes de Cousins Matter pueden gestionarse mediante un archivo `.env` situado en el directorio principal de la aplicación.

Si has utilizado el script manage_cousins_matter.py para instalar Cousins Matter tal como se describe en [Instalación](installation.md), un archivo .env de ejemplo se ha descargado automáticamente para ti y la SECRET_KEY y la POSTGRES_PASSWORD se han generado automáticamente (**¡no las sobrescribas!**).

Si trabajas a partir del código fuente, copia el archivo `.env.example` a `.env`

En ambos casos, ahora debes editar `.env` para definir las propiedades según tu contexto, tal como se describe a continuación.

Hay muchos ajustes disponibles para personalizar la parte técnica de tu sitio...

Además, no olvides consultar [Personalización](customizing.md) para personalizar el aspecto de tu sitio.

**ADVERTENCIA**: si el contenedor ya se está ejecutando, la actualización de los ajustes en .env no se tendrá en cuenta hasta que lo reinicies.
Para ello, simplemente ejecuta el siguiente comando (en el directorio del sitio):
```
docker compose restart
```

## Seguridad

* `SECRET_KEY`: una clave secreta que protege tu sitio. ¡Debe ser extravagantemente compleja y mantenerse en secreto! La forma más sencilla de generarla es ejecutar `python manage_cousins_matter.py rotate-secrets`. Este script también actualizará PREVIOUS_SECRET_KEYS en el archivo .env. Esta variable se utiliza para descodificar los tokens que se han enviado a los miembros con la clave secreta anterior.

	_(De nuevo, si utilizaste manage_cousins_matter.py para instalar Cousins Matter, esto ya se ha generado por ti, no lo sobrescribas)_
* `MAX_REGISTRATION_AGE`: validez máxima en segundos de los tokens de invitación; por defecto es de 2 días (2*24*3600)

## Superusuario

Antes de ejecutar `docker compose up -d` por primera vez, proporciona la información para crear el superusuario (es decir, la cuenta de administrador).

* `ADMIN`: el nombre de la cuenta del superusuario
* `ADMIN_PASSWORD`: la contraseña del superusuario
* `ADMIN_EMAIL`: el correo electrónico del superusuario
* `ADMIN_FIRSTNAME`: el nombre del superusuario
* `ADMIN_LASTNAME`: el apellido del superusuario

**TODAS ESTAS VARIABLES SON OBLIGATORIAS PARA CREAR LA CUENTA DEL SUPERUSUARIO Y NO TIENEN VALORES POR DEFECTO**

## Gestión de las funcionalidades

Puedes gestionar las funcionalidades que se ofrecerán a los miembros en el archivo .env.

Para ello, modifica la variable FEATURES_FLAGS basándote en el contenido del archivo .env.example y define como false el valor de cada funcionalidad que quieras ignorar.

El valor por defecto de FEATURES_FLAGS es:
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True;show_public_chats=True;show_private_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_site_stats=True;show_export_members=True;show_change_language=True;show_genealogy=True"
```

**Flags de funcionalidad disponibles:**

* `show_birthdays_in_homepage`: Mostrar los próximos cumpleaños en la página de inicio de los miembros autenticados
* `show_galleries`: Activar la función de galerías de fotos y vídeos
* `show_forums`: Activar los debates en el foro
* `show_public_chats`: Activar las salas de chat públicas
* `show_private_chats`: Activar las salas de chat privadas
* `show_classified_ads`: Activar la función de anuncios clasificados
* `show_polls`: Activar la función de encuestas
* `show_event_planners`: Activar las encuestas de planificación de eventos (encuestas de selección de fechas)
* `show_pages`: Activar la función de páginas CMS
* `show_treasures`: Activar la función de tesoros (tesoros familiares)
* `show_site_stats`: Mostrar la página de estadísticas del sitio
* `show_export_members`: Permitir la exportación del directorio de miembros a PDF
* `show_change_language`: Permitir el cambio de idioma en la interfaz
* `show_genealogy`: Activar las funciones de genealogía (árboles familiares, importación/exportación GEDCOM)

**ADVERTENCIAS:**

1. La variable INCLUDE_BIRTHDAYS_IN_HOMEPAGE ha sido sustituida por el flag de funcionalidad show_birthdays_in_homepage, como se muestra arriba.
2. FEATURES_FLAGS debe permanecer en una sola línea en el archivo .env. Todos los flags se separan con punto y coma. Si defines esta variable en tu archivo .env y un flag no está presente en la lista, se considera false.

## Personalización general

### Sitio

* `SITE_NAME`: el nombre del sitio; por defecto es 'Cousins Matter!'.
* `SITE_DOMAIN`: el dominio del sitio, p. ej. myfamily.com; sin valor por defecto.
* `SITE_FOOTER`: el pie de página opcional del sitio, p. ej. "The Simpsons Family Social Network".
* `SITE_LOGO`: la URL relativa opcional del logo de tu sitio (en la esquina superior izquierda). Debe tener una proporción de 4:1. **DEBE ALMACENARSE EN** la carpeta media/public de tu sitio, por lo que **la URL debe empezar por '/media/public'** (p. ej. SITE_LOGO='/media/public/my-own-logo.jpg')
* `SITE_COPYRIGHT`: el copyright de tu sitio, p. ej. 'Copyright © 2024 Cousins Matter'.
* `DARK_MODE`: activa el tema en modo oscuro. Por defecto es False.

### Miembros

* `ALLOW_MEMBERS_TO_CREATE_MEMBERS`: por defecto es True. Para impedir que los miembros creen y gestionen a otros miembros, define False y solo los administradores podrán hacerlo.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS`: por defecto es True. Para impedir que los miembros inviten a otros miembros a unirse al sitio, define False y solo los administradores podrán hacerlo.
* `BIRTHDAY_DAYS`: número de días en el futuro durante los que se muestran los cumpleaños; por defecto es 50
* ~~`INCLUDE_BIRTHDAYS_IN_HOMEPAGE`~~: **OBSOLETO** - Utiliza en su lugar `show_birthdays_in_homepage` en `FEATURES_FLAGS`
* `PDF_SIZE`: tamaño de página PDF del directorio impreso. Tamaño 'A4' o 'letter'. Por defecto es A4.
* `MAX_CSV_FILE_SIZE`(*): tamaño máximo del archivo CSV de importación de miembros; por defecto es 2MB.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP`: introduce aquí la IP externa de tu servidor. Se utiliza para el rastreo de conexiones cuando la conexión procede de la red interna. Por defecto es "8.8.8.8".
* `LOGIN_HISTORY_PURGE_DAYS`: número de días durante los que se conserva el historial de conexiones (visible para los administradores en el admin de Django); por defecto es 365.

### Galerías

* `DEFAULT_GALLERY_PAGE_SIZE`: número de fotos por página de galería (modificable en pantalla); por defecto es 25
* `MAX_PHOTO_FILE_SIZE`(*): tamaño máximo de cada foto; por defecto es 5MB
* `MAX_VIDEO_FILE_SIZE`(*): tamaño máximo de cada vídeo; por defecto es 20MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): tamaño máximo del archivo zip de carga en bloque de galerías; por defecto es 20MB
* `SLIDESHOW_DELAY`: intervalo en segundos entre cada foto en una proyección de diapositivas; por defecto es 5

### Mensajes y chats

* `MESSAGE_MAX_SIZE`(*): tamaño máximo de un mensaje en el foro o en los chats (ten en cuenta que puede contener una foto); por defecto es 2.5MB.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): tamaño máximo de un comentario asociado a un mensaje en el foro o en los chats; por defecto es 1000
* `CONTACT_MAX_SIZE`(*): tamaño máximo de un mensaje de contacto; por defecto es 1MB

### Páginas

* `PAGE_MAX_SIZE`(*): tamaño máximo de una página plana; por defecto es 10MB

### Encuestas

* `POLL_MAX_SIZE`(*): tamaño máximo de una encuesta; por defecto es 1MB

### Anuncios clasificados

* `CLASSIFIED_AD_MAX_SIZE`(*): tamaño máximo de un anuncio clasificado; por defecto es 1MB

### Tesoros

* `TROVE_FILE_MAX_SIZE`(*): tamaño máximo de un archivo de tesoro; por defecto es 20MB
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): tamaño máximo de una imagen de tesoro; por defecto es 5MB
* `TROVE_THUMBNAIL_SIZE`(*): tamaño máximo en píxeles de una miniatura de tesoro; por defecto es 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): número de tesoros por página por defecto; por defecto es 10

### Anuncios clasificados

* `MAX_PHOTO_PER_AD`: número máximo de fotos por anuncio clasificado; por defecto es 10

### Genealogía

* `FAMILY_CHART_GENERATIONS`: número de generaciones que se muestran hacia arriba y hacia abajo de la persona central en el árbol familiar; por defecto es 4
* `FAMILY_CHART_ROOT_PERSON_ID`: ID de la persona raíz por defecto que se muestra en el árbol familiar si no se especifica ninguna; por defecto es el id de la primera persona de la base de datos
* `GEDCOM_FILE`: archivo GEDCOM que se utilizará para exportar la genealogía; por defecto es 'genealogy.ged'

## Autenticación OAuth/SSO

* `OAUTH_PROVIDERS`: lista de proveedores OAuth separados por comas que se activarán. Proveedores disponibles: `google`, `facebook`, `apple`, `github`, `pocketid` o cualquier proveedor `openid_connect`. Por defecto está vacía (sin OAuth activado).
* `SOCIALACCOUNT_AUTO_SIGNUP`: si se exige una confirmación cuando un usuario inicia sesión con un proveedor OAuth. Por defecto es False (se requiere confirmación).

Para cada proveedor, debes definir:
* `<PROVIDER>_OAUTH_CLIENT_ID`: el client ID de OAuth para el proveedor
* `<PROVIDER>_OAUTH_CLIENT_SECRET`: el client secret de OAuth para el proveedor

Para los proveedores de OpenID Connect (incluido PocketID):
* `<PROVIDER>_SERVER_URL`: la URL del servidor de OpenID Connect

**Ejemplo de configuración:**
```
OAUTH_PROVIDERS=google,github,pocketid
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

Consulta [Autenticación OAuth](oauth-authentication.md) para ver las instrucciones de configuración detalladas de cada proveedor.

## Niveles de log

* `DJANGO_LOG_LEVEL`: nivel de log para django y las bibliotecas internas; por defecto es INFO
* `CM_LOG_LEVEL`: nivel de log para cousins matter; por defecto es INFO

## Configuración de red

* `ALLOWED_HOSTS`: lista de hosts separados por comas. Por defecto es '127.0.0.1,localhost,<SITE_DOMAIN\>'. __Debes definir ALLOWED_HOSTS en producción__ y __debe__ contener la URL completa de tu sitio y, a veces, dependiendo de la configuración de red de tu alojamiento, la IP general del sitio, p. ej.:

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: lista de hosts separados por comas. Por defecto está vacía.

	__¡ADVERTENCIA!__ Si tu log muestra errores tales como

	`Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

	deberías definir `CORS_ALLOWED_ORIGINS=<tu dominio completo>` (p. ej. https://my.cousins-matter.com) en el archivo `.env`,

	__¡No utilices la sintaxis de Python mostrada en el error!__.

	Si tienes varios hosts, enuméralos separados por comas, p. ej.

	`CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

	Como información, `CSRF_TRUSTED_ORIGINS` toma el valor de `CORS_ALLOWED_ORIGINS`

## Internacionalización

* `LANGUAGE_CODE`: p. ej. 'es' o 'es-MX'. Por defecto es 'en-US'.
* `TIME_ZONE`: zona horaria; por defecto es 'Europe/Paris'.

## Propiedades del correo electrónico

* `EMAIL_HOST`: nombre del host SMTP; sin valor por defecto
* `EMAIL_PORT`: puerto de conexión al servidor SMTP
* `EMAIL_USE_TLS`: el servidor SMTP utiliza STARTTLS si es true; por defecto es true
* `EMAIL_USE_SSL`: el servidor SMTP utiliza SSL si es true; por defecto es false
* `EMAIL_HOST_USER`: nombre de usuario para conectarse al servidor SMTP.
* `EMAIL_HOST_PASSWORD`: contraseña para conectarse al servidor SMTP
* `DEFAULT_FROM_EMAIL`: dirección de correo electrónico por defecto que se utilizará al enviar correos

## Base de datos

* `POSTGRES_USER`: el usuario de postgres; por defecto es 'cousinsmatter'
* `POSTGRES_PASSWORD`: la contraseña de postgres. Se genera automáticamente si utilizas manage_cousins_matter.py para instalar o migrar Cousins Matter. __¡ADVERTENCIA!__ Utiliza solo -_./* como caracteres especiales si quieres cambiarla. ¡Evita absolutamente : y @ !
* `POSTGRES_DB`: la base de datos de postgres; por defecto es 'cousinsmatter'
* `POSTGRES_HOST`: el host de postgres; por defecto es 'postgres'

* `REDIS_HOST`: el host de redis; por defecto es 'redis'

## Otros almacenamientos de medios

* `MEDIA_STORAGE` y `MEDIA_STORAGE_OPTIONS`: consulta [Almacenamiento de los medios](/media-storage.md)

## NOTAS

__(*) ADVERTENCIA:__ si quieres cambiar cualquiera de las variables que controlan el tamaño de lo que se puede subir y estás utilizando el proxy inverso nginx, comprueba que el valor de `client_max_body_size` en config/nginx/nginx.conf se mantenga por encima de las variables de tamaño que cambias arriba. De lo contrario, recibirás un error 413 de Nginx. El valor por defecto proporcionado es alto (20MB), pero puede que necesites aumentarlo para soportar vídeos más grandes.
