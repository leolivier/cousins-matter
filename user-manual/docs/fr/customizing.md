# Personnalisez votre site

## Paramètres
Consultez la page [Paramètres](settings.md) pour personnaliser votre site en modifiant les paramètres.

### Gestion des fonctionnalités
Grâce aux paramètres, vous pouvez également gérer les fonctionnalités qui seront proposées aux membres, comme expliqué dans la section [Gestion des fonctionnalités](settings.md/#features-management)

### Préférences de notification
Les membres peuvent configurer la fréquence des notifications par e-mail dans les paramètres de leur profil. Consultez la section [Fonctionnalités - Abonnés et notifications](features.md#abonnes-et-notifications) pour plus de détails.

## Création de pages
L'administrateur peut créer ou mettre à jour des pages statiques à l'aide de la fonctionnalité « Modifier la page » dans la barre de navigation. **Seuls les administrateurs ont accès à cette fonctionnalité !**

Lors de la création d’une page, un formulaire s’ouvre et vous devez remplir certains champs :

* URL : ce champ servira à afficher la page.
    Il existe différentes catégories de pages :

    * Les pages « À propos », y compris la politique de confidentialité décrite ci-dessous, doivent commencer par « /<code-langue\>/about/<slug-page\> ». Elles s’affichent à droite de la barre de navigation, sous une icône en forme de point d’interrogation.
	* Les pages « Accueil » sont des pages commençant par « /<code-langue\>/home/ ». Voir [Page d’accueil](#front-or-home-pages) ci-dessous
    * Les pages « Statiques » sont des pages commençant par « /publish/ ». Elles peuvent comporter deux sous-formulaires :

		* /publish/<slug-de-page\> : le titre de ces pages s’affiche directement dans le menu « Pages » de la barre de navigation.
        * /publish/<nom-de-menu\>/<slug-de-page\> : il s’agit de menus déroulants du menu « Pages » portant le nom « nom-de-menu », et le titre de chaque page s’affiche dans la liste déroulante sous <nom-de-menu\>.

	* Pages de message, dont l’URL commence par « /admin-message/ » ; voir [Afficher un message d’administration sur toutes les pages](#show-an-admin-message-on-all-pages)
    * Toute autre URL peut être incluse sous forme de lien dans d’autres pages, mais ne sera pas accessible depuis la barre de menu.

* Titre : il s’agit de la chaîne de caractères qui s’affichera dans les menus.
* Contenu : il s’agit du contenu de la page. Il peut être modifié à l’aide de l’éditeur enrichi.
* Une case à cocher intitulée « Autoriser les commentaires » est affichée mais n’est pas utilisée pour le moment.

## Gestion de la confidentialité
Des pages statiques (une par langue) décrivant la politique de confidentialité du site sont chargées dans la base de données lors de l’installation de l’application.
Ces pages peuvent être personnalisées à l’aide de la fonctionnalité standard « Modifier la page » décrite ci-dessus.

**AVERTISSEMENT** : ne modifiez pas l'URL de ces pages ! Le modèle de cette URL est /<code-langue\>/about/privacy-policy. Si vous modifiez ce modèle, la politique de confidentialité associée ne sera plus accessible !

## Pied de page personnalisé
Définissez `SITE_FOOTER` comme expliqué dans [Personnalisation générale](settings.md/#general-customization)

## Pages d’accueil
Votre site a besoin de deux pages d’accueil différentes :

* La première destinée aux visiteurs non authentifiés, où vous pouvez expliquer l’objectif de votre site sans donner trop de détails ni d’informations confidentielles.
* La seconde est la page destinée à vos membres une fois qu’ils sont connectés.
Vous pouvez modifier ces deux pages directement depuis la page d’accueil par défaut ou depuis la liste des pages dans le menu.

L’URL de ces pages est construite comme suit : /<code de langue\>/home/authenticated et /<code de langue\>/home/unauthenticated.

Des versions prédéfinies de ces deux pages sont chargées dans la base de données lors du premier chargement.
Si le code de langue dans le fichier .env ne correspond à aucune des pages préchargées, c'est la version en-US qui s'affiche.

**ATTENTION** : ne modifiez pas les URL de ces pages, sinon cela ne fonctionnera pas !!!

## Afficher un message d'administration sur toutes les pages
Les administrateurs peuvent créer des pages spéciales dont l'URL commence par « /admin-message/ ». Le titre de cette page ne sera utilisé que dans la liste des pages du menu « Modifier les pages ». Le contenu de ces pages s'affiche sous forme de notification en haut de chaque page ; il peut être fermé, mais réapparaîtra à chaque nouvelle connexion tant que la page existe dans la base de données.

Vous pouvez créer soit une seule page avec l’URL « /admin-message/ », soit un nombre illimité de pages commençant toutes par « /admin-message/ » ; chaque page s’affichera alors sous forme d’une notification spécifique.

## Thèmes
Pour créer votre propre thème, vous devez attribuer de nouvelles valeurs aux variables Bulma dans le fichier nommé media/public/theme.css (ce fichier est intégré aux images Docker).

La personnalisation doit respecter le format suivant :

```
:root {
    --bulma-xxx: valeur;
    --bulma-yyy: valeur;
    --bulma-zzz: valeur;
}
```

Par exemple :

```
:root {
    --bulma-body-font-size: 16px;
    --bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
    --bulma-primary-l: 37% !important;
}
```

modifiera la taille de police globale du site et changera la couleur principale (définie en termes de HSL (teinte, saturation et luminosité)).
(Vous pouvez tester les couleurs HSL sur https://hslpicker.com/)

Vous pouvez également modifier ces variables au niveau du composant, mais dans ce cas, il ne s’agit plus d’un véritable thème. Pour plus de détails, consultez les pages [Variables CSS de Bulma](https://bulma.io/documentation/features/css-variables/) et [Personnalisation de Bulma avec les variables CSS](https://bulma.io/documentation/customize/with-css-variables/)

Pour connaître toutes les variables CSS disponibles définies par Bulma, veuillez consulter le [fichier CSS de Bulma](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) et testez-les dans votre navigateur pour voir le résultat.
