# Authentification OAuth/SSO

## Introduction

Cousins Matter prend en charge l’authentification via OAuth2/OpenID Connect avec plusieurs fournisseurs. Cela permet aux membres de se connecter à l’aide de leurs comptes existants sur des services populaires tels que Google, Facebook, GitHub, etc.
**IMPORTANT** : Le lien entre le compte du fournisseur d’identité OAuth et Cousins Matter est établi à l’aide de l’adresse e-mail du membre.

## Conditions préalables

* Les membres doivent disposer d’une invitation valide pour s’inscrire via OAuth
* Les fournisseurs OAuth doivent être configurés dans le fichier `.env`
* Chaque fournisseur nécessite un identifiant client et une clé secrète client

## Configuration

### Activer les fournisseurs OAuth

Dans votre fichier `.env`, définissez la liste des fournisseurs que vous souhaitez activer :

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Fournisseurs disponibles :
* `google` - OAuth Google
* `facebook` - OAuth Facebook
* `apple` - Connexion Apple
* `github` - OAuth GitHub
* `pocketid` - PocketID (OpenID Connect)
* Tout autre fournisseur compatible avec OpenID Connect

### Configuration de l’inscription automatique

Déterminez si les utilisateurs doivent confirmer leur connexion lorsqu’ils utilisent OAuth :

```bash
# Exiger une confirmation (recommandé pour des raisons de sécurité)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Autoriser l'inscription automatique sans confirmation
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Par défaut :** `False` (confirmation requise)

## Configuration spécifique aux fournisseurs

### OAuth Google

1. Créez un projet dans la [Console Google Cloud](https://console.cloud.google.com/)
2. Activez l’API Google+
3. Créez des identifiants OAuth 2.0
4. Ajoutez les URI de redirection autorisées : `https://yourdomain.com/accounts/google/login/callback/`

Configuration dans `.env` :
```bash
GOOGLE_OAUTH_CLIENT_ID=votre_id_client_google
GOOGLE_OAUTH_CLIENT_SECRET=votre_secret_client_google
```

### OAuth Facebook

1. Créez une application dans [Facebook Developers](https://developers.facebook.com/)
2. Ajoutez le produit « Connexion Facebook »
3. Configurez les URI de redirection OAuth valides : `https://yourdomain.com/accounts/facebook/login/callback/`

Configuration dans le fichier `.env` :
```bash
FACEBOOK_OAUTH_CLIENT_ID=votre_id_d'application_Facebook
FACEBOOK_OAUTH_CLIENT_SECRET=votre_secret_d'application_Facebook
```

### Connexion via Apple

1. Enregistrez votre application sur le [Portail des développeurs Apple](https://developer.apple.com/)
2. Créez un identifiant de service
3. Configurez la connexion via Apple

Configuration dans le fichier `.env` :
```bash
APPLE_OAUTH_CLIENT_ID=votre_identifiant_de_service_apple
APPLE_OAUTH_CLIENT_SECRET=votre_secret_client_apple
```

### OAuth GitHub

1. Enregistrez une nouvelle application OAuth dans les [paramètres GitHub](https://github.com/settings/developers)
2. Définissez l’URL de rappel d’autorisation : `https://yourdomain.com/accounts/github/login/callback/`

Configuration dans `.env` :
```bash
GITHUB_OAUTH_CLIENT_ID=votre_id_client_github
GITHUB_OAUTH_CLIENT_SECRET=votre_secret_client_github
```

### PocketID (OpenID Connect)

[PocketID](https://pocketid.app/) est un fournisseur OpenID Connect auto-hébergé.

Configuration dans `.env` :
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=votre_identifiant_client_pocketid
POCKETID_OAUTH_CLIENT_SECRET=votre_secret_client_pocketid
```

### Fournisseur OpenID Connect générique

Pour tout autre fournisseur compatible OpenID Connect :

Configuration dans le fichier `.env` :
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=votre_identifiant_client
OPENID_CONNECT_OAUTH_CLIENT_SECRET=votre_secret_client
```

## Processus d’invitation

L’authentification OAuth dans Cousins Matter nécessite une invitation valide :

1. **Pour les nouveaux utilisateurs :**
   * Un administrateur ou un membre autorisé doit envoyer une invitation à l’adresse e-mail de l’utilisateur
   * L’utilisateur clique sur le lien d’invitation
   * L’invitation est stockée dans la session
   * L’utilisateur peut alors s’authentifier via OAuth
   * Le compte est automatiquement activé

2. **Pour les utilisateurs existants inactifs :**
   * Si un compte utilisateur existe mais n’est pas actif
   * L’utilisateur doit utiliser le lien d’invitation envoyé à son adresse e-mail
   * Après avoir cliqué sur le lien, il peut s’authentifier via OAuth
   * Le compte est activé et associé au fournisseur OAuth

3. **Pour les utilisateurs actifs :**
   * Les utilisateurs actifs peuvent se connecter directement via OAuth
   * Aucune invitation n’est requise
   * Le compte OAuth est associé à leur compte existant

## Considérations de sécurité

* **Vérification par e-mail :** les fournisseurs OAuth doivent fournir une adresse e-mail
* **Invitation requise :** les nouveaux utilisateurs ne peuvent pas s’inscrire eux-mêmes sans invitation
* **Sécurité de la session :** les jetons d’invitation sont stockés en toute sécurité dans la session
* **Expiration des jetons :** les jetons d’invitation expirent après une période configurable (voir `MAX_REGISTRATION_AGE` dans [Paramètres](settings.md))

## Dépannage

### « Aucune invitation trouvée pour cette adresse e-mail »

Cette erreur se produit lorsque :
* L’utilisateur n’a pas cliqué sur un lien d’invitation
* L’invitation a expiré
* L’e-mail provenant du fournisseur OAuth ne correspond pas à l’adresse e-mail de la personne invitée

**Solution :** Demandez une nouvelle invitation à un administrateur en indiquant l’adresse e-mail correcte.

### « Le fournisseur d’identité n’a pas fourni d’adresse e-mail »

Certains fournisseurs OAuth peuvent ne pas partager l’adresse e-mail.

**Solution :** Configurez le fournisseur OAuth pour inclure l'adresse e-mail dans le champ d'application.

### « Ce compte n'est pas encore actif »

Le compte utilisateur existe mais n'a pas encore été activé.

**Solution :** Utilisez le lien d'invitation envoyé par e-mail avant de tenter une connexion via OAuth.

## Redémarrage requis

Après avoir modifié les paramètres OAuth dans `.env`, redémarrez Cousins Matter :

```bash
docker compose restart
```

## Voir aussi

* [Paramètres](settings.md) - Référence complète des paramètres
* [Installation](installation.md) - Configuration initiale
* [Fonctionnalités](features.md) - Fonctionnalités de gestion des membres
