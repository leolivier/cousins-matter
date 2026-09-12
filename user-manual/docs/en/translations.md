# Translations

## Available translations

Cousins Matter comes with English, French, Spanish, Italian, German and Italian translations.

The language can be changed dynamically in the gear wheel menu.

**WARNING**: As these translations are mostly produced using AI, they may occasionally be inaccurate. If you find any errors, please open an issue on GitHub.


## Translate to a new language

The Cousins Matter website can easily be translated into any Latin LTR language by following the steps below. Not tested for RTL or non latin languages.

* Clone the Cousins Matter repository:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

* Generate the translation files:

	```
	python manage.py makemessages -l <language_code>
	```

* Edit the django.po files in the locale folder of each app.

	To find them, use the following command:

	```
	ls */locale/<language_code>/LC_MESSAGES/*.po
	```

* Compile the translations:

	```
	python manage.py compilemessages
	```

* Build the docker image:

	```
	docker build -t cousins-matter:<your tag> .
	```

	Don't forget to set COUSINS_MATTER_IMAGE to your tag in the .env file before restarting the container.

* Please, open an issue on GitHub to add your translation to the repository. Thank you!
