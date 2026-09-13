## Fonctionnalités

### Gestion des membres

* Les membres peuvent être répertoriés, filtrés par prénom et nom, et triés

    ![members](assets/members.webp)

* L'administrateur du site ou n'importe quel membre (selon les paramètres) peut inviter d'autres membres par e-mail

    ![invite](assets/invite.webp)

* Tout le monde peut demander une invitation, qui sera envoyée par e-mail à l'administrateur du site, lequel pourra alors l'inviter. Les demandes d'invitation sont protégées par un captcha.

    ![request-invite](assets/request-invite.webp)

* Les membres peuvent créer des membres « gérés », c'est-à-dire des membres qui ne sont pas actifs sur le site (par exemple, pour les jeunes enfants ou les personnes âgées)
* Les membres gérés peuvent être activés par les membres qui les gèrent (par exemple, lorsqu'un enfant est en âge d'être actif sur le site).
* Les membres peuvent être importés en masse via des fichiers CSV
* Les membres peuvent mettre à jour leur propre profil ainsi que celui des membres qu'ils gèrent
* Les membres peuvent être signalés comme décédés avec une date de décès (utile pour la généalogie et l'histoire familiale)

    ![profil](assets/profile.webp)

* Un annuaire des membres peut être imprimé au format PDF

    ![annuaire](assets/directory.webp)

* Les anniversaires des 50 prochains jours peuvent être affichés (le nombre de 50 peut être modifié dans les paramètres)

    ![anniversaires](assets/birthdays.webp)

### Authentification

* Authentification standard par e-mail et mot de passe
* Authentification OAuth/SSO avec plusieurs fournisseurs :
    * Google
    * Facebook
    * Apple
    * GitHub
    * PocketID (OpenID Connect auto-hébergé)
    * Tout fournisseur compatible avec OpenID Connect
* Voir [Authentification OAuth](oauth-authentication.md) pour une configuration détaillée

### Sécurité et historique des connexions

* Toutes les tentatives de connexion sont automatiquement suivies avec géolocalisation par adresse IP
* L’historique des connexions est conservé à des fins d’audit de sécurité (visible par les administrateurs du site dans l’interface d’administration Django)
* Suppression automatique des anciens enregistrements de connexion après une période de conservation configurable
* Aide les administrateurs à détecter les tentatives d’accès non autorisées

### Abonnés et notifications

* Les membres peuvent s’abonner à d’autres membres pour être informés de leurs activités
* Les membres peuvent suivre des salons de discussion, des forums, des galeries et d’autres contenus
* Notifications automatiques par e-mail lorsque le contenu suivi est mis à jour
* Fréquence de notification configurable par membre :
    * **Immédiate** - Recevoir des notifications dès que des événements se produisent
    * **Toutes les heures** - Recevoir un résumé des événements toutes les heures
    * **Quotidienne** - Recevoir un récapitulatif quotidien des événements
	* **Hebdomadaire** : recevoir un résumé hebdomadaire
    * **Mensuel** : recevoir un résumé mensuel
    * **Jamais** : désactiver complètement les notifications
* Chaque membre peut configurer la fréquence de notification de son choix dans les paramètres de son profil
* Le regroupement des notifications réduit la surcharge d'e-mails tout en tenant les membres informés

### Galeries

* Tous les membres actifs peuvent créer des galeries et y ajouter des photos et des vidéos
* Les galeries peuvent comporter des sous-galeries à n'importe quel niveau de hiérarchie
* Les photos et vidéos peuvent être importées en masse à l'aide de fichiers ZIP. Chaque dossier du fichier ZIP devient une galerie. Les mises à jour sont gérées
* L'affichage des photos dans les galeries est paginé
* Les photos et vidéos peuvent être affichées en mode plein écran et sous forme de diaporama avec un délai configurable

### Forum

* Les membres actifs peuvent créer des messages
* Les membres actifs peuvent répondre aux messages des autres membres ou ajouter des commentaires simples

### Chat

* Les membres connectés peuvent discuter en direct avec d’autres membres connectés
* Cousins Matter gère autant de salons de discussion que nécessaire
* Les membres peuvent créer des salons de discussion privés et sélectionner les membres autorisés à y participer.
    Le créateur du salon devient administrateur de celui-ci et peut ajouter d’autres membres ainsi que désigner des administrateurs parmi ces derniers.
	Les administrateurs peuvent inviter d’autres membres et d’autres administrateurs

### Pages / CMS

Fonctionnalités de base du CMS : les administrateurs peuvent créer des pages HTML statiques et les publier sur le site.
La page d’accueil peut également être configurée de cette manière, tout comme la politique de confidentialité, les pages « À propos »…
Les pages publiques (celles qui s’affichent dans le menu « Pages » même si vous n’êtes pas connecté) peuvent être créées et publiées par n’importe quel membre administrateur. Leur URL doit commencer par « /publish/ »
Les pages privées (celles qui s’affichent dans le menu « Pages » uniquement si vous êtes connecté) peuvent être créées et publiées par n’importe quel administrateur. Leur URL doit commencer par « /private/ »
Les messages d’administration constituent un type spécifique de page qui s’affiche en haut du site pour tous les membres connectés. Leur URL doit commencer par « /admin-message/ »
D'autres pages spécifiques par défaut peuvent être modifiées par n'importe quel administrateur. Elles sont accessibles depuis le menu d'administration sous « Modifier les pages » et affichent respectivement la page d'accueil lorsque vous n'êtes pas connecté (/home/unauthenticated/\<lang>), lorsque vous êtes connecté (/home/authenticated/\<lang>), ainsi que la politique de confidentialité (/about/privacy-policy/\<lang>).

### Trésors

Cet espace vous permet de mettre en avant les trésors numériques de votre famille, qu’il s’agisse de textes, de musique ou de vidéos.

### Sondages

Tout membre actif peut créer un sondage et tout membre actif peut répondre à un sondage en cours.
Les sondages ont une date de publication et une date de clôture. Ils peuvent comporter plusieurs questions, qui peuvent prendre les formes suivantes :

* questions simples de type oui/non : cocher la case
* texte libre : saisir le texte enrichi de votre choix
* date : sélectionner une date
* choix : sélectionner une option dans une liste


### Organisation d'événements

En tant que sous-module du module « Sondage », tout membre actif peut créer un sondage d'organisation d'événement afin de déterminer la date à laquelle un événement doit avoir lieu. Cela ajoute au module « Sondage » les types de choix suivants :

* choisir une date dans une liste proposée
* choisir plusieurs dates dans une liste proposée

### Petites annonces

Tout membre actif peut publier une petite annonce visible par tous les autres membres. Si un membre est intéressé par une annonce, il peut envoyer un message à son auteur, qui recevra alors un e-mail.

### Généalogie

Tout membre actif peut ajouter des personnes à la généalogie du site. Vous pouvez ajouter des personnes à la généalogie en saisissant leurs données dans des formulaires ou en important un fichier GEDCOM. Vous pouvez exporter la généalogie au format GEDCOM. La généalogie peut être affichée sous forme d’arbre dynamique ou de listes de personnes ou de familles.
