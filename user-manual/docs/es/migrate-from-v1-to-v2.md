# Migrar de la versión 1 a la versión 2

## Introducción

La versión 2 de Cousins Matter es una reescritura en profundidad de la versión 1 y no es directamente compatible con la versión 1.
Entre los grandes cambios:

* la base de datos se ha migrado de sqlite3 a postgresql para permitir un mejor rendimiento y una mayor escalabilidad.
* cousins matter se compone ahora de al menos 4 contenedores de docker:

	* el servidor web
	* la base de datos
	* redis
	* el servidor de tareas asíncronas

	y por lo tanto necesitará docker compose para ejecutarse.

## Requisitos previos

Debes tener Cousins Matter v1 instalado y funcionando en tu sistema.

También necesitarás un entorno Python 3.14+ para ejecutar el script de migración.

## Procedimiento

1. Detén Cousins Matter v1

	```
	cd <cousins-matter-v1-directory>
	docker compose down
	```

1. Descarga el script de administración de Cousins Matter

	Por favor, sustituye en el enlace de abajo el marcador de posición <release\> por la versión actual de Cousins Matter:
![GitHub Release](https://img.shields.io/github/v release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
	mkdir scripts
	curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
	```

1. Ejecuta el script de migración

	```
	python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <release>]
	```

	Si no se indica la versión, se migrará a la última versión de v2.X (recomendado).

	**¡Presta atención al log del script de migración!** Te mostrará el progreso de la migración y cualquier posible problema o acción a realizar.

1. Actualiza tus ajustes

	Los ajustes de Cousins Matter v2 son diferentes de los de la v1. Por favor, actualiza tu archivo .env para que se ajuste a los ajustes de Cousins Matter v2.

	Los ajustes de Cousins Matter v2 se detallan en la página [Ajustes](settings.md).
	En particular, la migración actualiza el archivo .env.example para que se ajuste a los ajustes de Cousins Matter v2. Así que, por favor, compara este nuevo archivo .env.example con tu archivo .env y actualiza tu archivo .env en consecuencia.

	Presta también atención a que algunos valores por defecto han cambiado. Por ejemplo:

	* ALLOW_MEMBERS_TO_CREATE_MEMBERS y ALLOW_MEMBERS_TO_INVITE_MEMBERS son ahora True por defecto
	* ALLOWED_HOSTS contiene ahora, por defecto, el valor de SITE_DOMAIN ('127.0.0.1,localhost,$SITE_DOMAIN')
	* DARK_MODE es ahora False por defecto
	* SESSION_COOKIE_DOMAIN se define ahora, por defecto, como .$SITE_DOMAIN
	* SITE_PORT se define ahora como 0 si SITE_DOMAIN está definido, y 8000 si no

	Asimismo, se han añadido nuevas variables al archivo .env, pero tienen valores por defecto razonables.

	* POSTGRES_USER=cousinsmatter
	* POSTGRES_DB=cousinsmatter
	* POSTGRES_HOST=postgres
	* POSTGRES_PASSWORD se calcula automáticamente en el momento de la migración
	* PREVIOUS_SECRET_KEYS se calcula automáticamente en el momento de la migración (y la SECRET_KEY se rota)

1. Inicia Cousins Matter v2

	```
	docker compose pull  # obtener todas las imágenes
	docker compose up -d
	```
