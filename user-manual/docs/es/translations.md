# Traducciones

## Traducciones disponibles

Cousins Matter incluye traducciones en inglés, francés, español, italiano, alemán e italiano.

El idioma puede cambiarse dinámicamente en el menú de la rueda dentada.

**ADVERTENCIA**: como estas traducciones se han producido principalmente con IA, pueden ser ocasionalmente imprecisas. Si encuentras algún error, por favor abre un issue en GitHub.


## Traducir a un nuevo idioma

El sitio web Cousins Matter puede traducirse fácilmente a cualquier idioma latino de izquierda a derecha (LTR) siguiendo los pasos indicados a continuación. No se ha probado con idiomas RTL o no latinos.

* Clona el repositorio de Cousins Matter:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

* Genera los archivos de traducción:

	```
	python manage.py makemessages -l <language_code>
	```

* Edita los archivos django.po en la carpeta locale de cada aplicación.

	Para encontrarlos, utiliza el siguiente comando:

	```
	ls */locale/<language_code>/LC_MESSAGES/*.po
	```

* Compila las traducciones:

	```
	python manage.py compilemessages
	```

* Construye la imagen de docker:

	```
	docker build -t cousins-matter:<your tag> .
	```

	No olvides definir COUSINS_MATTER_IMAGE con tu etiqueta en el archivo .env antes de reiniciar el contenedor.

* Por favor, abre un issue en GitHub para añadir tu traducción al repositorio. ¡Gracias!
