# Instalación de Cousins Matter

Esto se ha probado en Linux y en Windows+WSL2 con Ubuntu o Debian + Docker Desktop instalado. (El script de instalación aún no se ha probado en MacOS, pero debería funcionar con muy pocos cambios)

## Instalación en producción

### Requisitos previos

Si aún no lo has hecho, instala Docker en tu servidor:
```
curl https://get.docker.com | sh
```

También necesitarás un entorno Python 3.14+ para ejecutar el script de administración de Cousins Matter.

### Descargar y ejecutar el script de administración de Cousins Matter

Por favor, sustituye en el enlace de abajo el marcador de posición **<release\>** por la versión actual de Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <directory>] [-r <release>]
```

* si no se indica el directorio con -d, la instalación se realizará en el directorio actual
* si no se indica la versión con -r, se instalará la última versión

Este comando:

* descargará los archivos necesarios de Cousins Matter;
* creará los directorios necesarios;
* creará el archivo .env base a partir de un ejemplo;
* abrirá un editor con el archivo .env para que lo adaptes a tus necesidades (consulta la página [Ajustes](settings.md)). En particular, __no olvides añadir la información para crear el superusuario__.

Este script también puede ayudarte a [migrar de la v1 a la v2 de Cousins Matter](migrate-from-v1-to-v2.md) y a [rotar tu clave secreta de vez en cuando](other-management-operations.md#rotar-tu-clave-secreta).

Para ver los diferentes comandos disponibles, ejecuta:

```
python manage_cousins_matter.py -h
```

Para obtener ayuda sobre un comando específico, ejecuta:

```
python manage_cousins_matter.py <command> -h
```


### Iniciar Cousins Matter

```
cd <directory>
docker compose up -d
```

__La primera vez__, ve a http://127.0.0.1:8000/members/profile, inicia sesión con la cuenta de administrador que acabas de crear y completa tu perfil.

**¡Y ya está!**

## Construir a partir del código fuente

* Instala Docker y uv si aún no lo has hecho

	```
	curl https://get.docker.com | sh
  pip install uv
	```

* Clona el repositorio git:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

**Nota para los colaboradores:** si quieres contribuir al desarrollo de cousins-matter, primero haz un fork del proyecto en github y clona tu propio repositorio.

* Crea y sincroniza tu entorno virtual de python:
  ```
  uv sync
	```

* Actualiza tus ajustes:
	Copia `.env.example` a `.env` y edita `.env` para definir las propiedades según tus necesidades; consulta la página [Ajustes](settings.md).

	Puedes crear automáticamente la SECRET_KEY ejecutando el siguiente comando:

	```
	./manage_cousins_matter.sh rotate-secrets
	```

* construye la imagen de docker:

	```
	make build t=cousins-matter:local
	```

* Utiliza tu imagen local añadiendo la siguiente línea al archivo .env:
	```
	COUSINS_MATTER_IMAGE=cousins-matter:local
	```

* Inicia todo:

	```
	make up
	```

### Ejecutarlo fuera de Docker

Si quieres depurar tu instalación, puedes ejecutarla fuera de Docker.

Para ello, en lugar de lanzar `make up`, utiliza:
```
make up4run  # iniciará los contenedores necesarios: postgres, redis y qcluster (usando la imagen construida previamente)
# para iniciar cousins-matter en modo desarrollo
make run  # se recargará automáticamente tras cada modificación del código
# para ejecutar los tests (sin los tests de UI)
make test [t=<test name>]
# para ejecutar los tests de UI
make test-ui [t=<test name>]
# para obtener todos los demás comandos de make, simplemente ejecuta
make
```
o inicia la depuración desde tu IDE (el proyecto ya está configurado para Visual Studio Code en el archivo .vscode/launch.json)
