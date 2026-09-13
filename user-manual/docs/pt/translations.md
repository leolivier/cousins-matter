# Traduções

## Traduções disponíveis

O Cousins Matter é fornecido com traduções em inglês, francês, espanhol, italiano, alemão e italiano.

O idioma pode ser alterado dinamicamente no menu da roda dentada.

**AVISO**: as traduções são produzidas maioritariamente por IA e podem ocasionalmente ser imprecisas. Se encontrar erros, abra um issue no GitHub.


## Traduzir para um novo idioma

O sítio web do Cousins Matter pode ser facilmente traduzido para qualquer idioma latino LTR seguindo os passos abaixo. Não testado para idiomas RTL ou não latinos.

* Clone o repositório do Cousins Matter:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

* Gere os ficheiros de tradução:

	```
	python manage.py makemessages -l <language_code>
	```

* Edite os ficheiros django.po na pasta locale de cada aplicação.

	Para os localizar, utilize o seguinte comando:

	```
	ls */locale/<language_code>/LC_MESSAGES/*.po
	```

* Compile as traduções:

	```
	python manage.py compilemessages
	```

* Construa a imagem docker:

	```
	docker build -t cousins-matter:<your tag> .
	```

	Não se esqueça de definir COUSINS_MATTER_IMAGE com a sua etiqueta no ficheiro .env antes de reiniciar o contentor.

* Por favor, abra um issue no GitHub para acrescentar a sua tradução ao repositório. Obrigado!
