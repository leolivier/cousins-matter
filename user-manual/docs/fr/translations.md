# Traductions

## Traductions disponibles

Cousins Matter est disponible en anglais, français, espagnol, italien et allemand.

La langue peut être modifiée à la volée dans le menu représenté par une roue dentée.

**AVERTISSEMENT** : ces traductions étant pour la plupart générées par l’IA, elles peuvent parfois comporter des inexactitudes. Si vous constatez des erreurs, merci de créer un ticket sur GitHub.


## Traduire vers une nouvelle langue

Le site web de Cousins Matter peut facilement être traduit dans n’importe quelle langue latine LTR en suivant les étapes ci-dessous. Non testé pour les langues RTL ou non latines.

* Clonez le dépôt Cousins Matter :

    ```
    git clone https://github.com/leolivier/cousins-matter.git
    cd cousins-matter
    ```

* Générez les fichiers de traduction :

	```
    python manage.py makemessages -l <code_langue>
    ```

* Modifiez les fichiers django.po dans le dossier locale de chaque application.

    Pour les localiser, utilisez la commande suivante :

    ```
    ls */locale/<code_langue>/LC_MESSAGES/*.po
    ```

* Compilez les traductions :

    ```
	python manage.py compilemessages
    ```

* Construisez l’image Docker :

    ```
    docker build -t cousins-matter:<votre balise> .
    ```

    N’oubliez pas de définir COUSINS_MATTER_IMAGE sur votre balise dans le fichier .env avant de redémarrer le conteneur.

* Veuillez ouvrir un ticket sur GitHub pour ajouter votre traduction au dépôt. Merci !
