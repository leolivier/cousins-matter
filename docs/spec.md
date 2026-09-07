# création d'un tenant par une personne:

Ceci est un projet parallèle et complémentaire du projet cousins-matter. Il doit être développé dans un repo gothub **privé** à côté de cousins-matter

- toute personne peut créer un nouveau tenant à partir d'un site cousins-matter.net (domaine à valider)
- La page d'accueil du site décrit cousins-matter, la variante self-hosted (en pointant vers le site cousins-matter.readthedocs.io pour les détails), fournit un lien vers le site de démo (lien à définir) et décrit la version SaaS avec le version gratuite et ses limites. Plus tard, cet écran permettra de proposer la version payante avec une comparaison des features gratuites/payantes
- Un bouton permet de demander la crétion d'un tenant
- pour cela, il faut d'abord passer par un captcha pour bloquer les robots
- la personne doit ensuite fournir un email et donner un nom de tenant (nom de la famille du site) dont l'unicité sera vérifiée au fur et à mesure (lettre à lettre).
- une fois la demande soumise, un mail de vérification avec lien est envoyé sur le mail fourni (validité 24h)
- le nom de tenant reste réservé pendant ces 24h. Puis il est rendu disponible s'il n'a pas été validé
- une fois validé par le clic dans le lien, le tenant est créé automatiquement et le compte de l'admin du tenant est créé automatiquement aussi. 
- Ensuite, il est proposé à l'admin un petit parcours de découverte de son site incluant:
  - l'écran de paramètres du tenant, 
  - le profil de l'admin à compléter
  - l'écran pour inviter des membres.

**NOTE:** la page de base des sites avec tenant dans cousins-matter et sans sous domaines ne peut plus être différenciée avant login (sauf par cookie?)
