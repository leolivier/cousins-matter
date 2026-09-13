# Autenticação OAuth/SSO

## Introdução

O Cousins Matter suporta a autenticação via OAuth2/OpenID Connect com vários fornecedores. Isto permite que os membros iniciem sessão utilizando as suas contas existentes de serviços populares como Google, Facebook, GitHub e outros.
**IMPORTANTE**: a ligação entre a conta do fornecedor de identidade OAuth e o Cousins Matter é estabelecida utilizando o endereço de e-mail do membro.

## Pré-requisitos

* Os membros têm de ter um convite válido para se registarem via OAuth
* Os fornecedores OAuth têm de estar configurados no ficheiro `.env`
* Cada fornecedor exige um client ID e um client secret

## Configuração

### Ativar os fornecedores OAuth

No seu ficheiro `.env`, defina a lista de fornecedores que pretende ativar:

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Fornecedores disponíveis:
* `google` - OAuth da Google
* `facebook` - OAuth da Facebook
* `apple` - Apple Sign In
* `github` - OAuth do GitHub
* `pocketid` - PocketID (OpenID Connect)
* Qualquer outro fornecedor compatível com OpenID Connect

### Configuração do registo automático

Controle se os utilizadores têm de confirmar o seu início de sessão quando utilizam o OAuth:

```bash
# Exigir confirmação (recomendado por razões de segurança)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Permitir o registo automático sem confirmação
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Predefinição:** `False` (confirmação exigida)

## Configuração específica de cada fornecedor

### OAuth da Google

1. Crie um projeto na [Google Cloud Console](https://console.cloud.google.com/)
2. Ative a API Google+
3. Crie credenciais OAuth 2.0
4. Acrescente os URIs de redirecionamento autorizados: `https://yourdomain.com/accounts/google/login/callback/`

Configuração no `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### OAuth da Facebook

1. Crie uma aplicação em [Facebook Developers](https://developers.facebook.com/)
2. Acrescente o produto Facebook Login
3. Configure os Valid OAuth Redirect URIs: `https://yourdomain.com/accounts/facebook/login/callback/`

Configuração no `.env`:
```bash
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret
```

### Apple Sign In

1. Registe a sua aplicação no [Apple Developer Portal](https://developer.apple.com/)
2. Crie um Service ID
3. Configure o Sign In with Apple

Configuração no `.env`:
```bash
APPLE_OAUTH_CLIENT_ID=your_apple_service_id
APPLE_OAUTH_CLIENT_SECRET=your_apple_client_secret
```

### OAuth do GitHub

1. Registe uma nova aplicação OAuth em [GitHub Settings](https://github.com/settings/developers)
2. Defina o Authorization callback URL: `https://yourdomain.com/accounts/github/login/callback/`

Configuração no `.env`:
```bash
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

### PocketID (OpenID Connect)

O [PocketID](https://pocketid.app/) é um fornecedor de OpenID Connect auto-hospedado.

Configuração no `.env`:
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

### Fornecedor genérico de OpenID Connect

Para qualquer outro fornecedor compatível com OpenID Connect:

Configuração no `.env`:
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=your_client_id
OPENID_CONNECT_OAUTH_CLIENT_SECRET=your_client_secret
```

## Processo de convite

A autenticação OAuth no Cousins Matter exige um convite válido:

1. **Para novos utilizadores:**
   * Um administrador ou um membro autorizado tem de enviar um convite para o e-mail do utilizador
   * O utilizador clica na hiperligação do convite
   * O convite é guardado na sessão
   * O utilizador pode então autenticar-se via OAuth
   * A conta é ativada automaticamente

2. **Para utilizadores existentes inativos:**
   * Se uma conta de utilizador existe mas não está ativa
   * O utilizador tem de utilizar a hiperligação de convite enviada para o seu e-mail
   * Depois de clicar na hiperligação, pode autenticar-se via OAuth
   * A conta é ativada e ligada ao fornecedor OAuth

3. **Para utilizadores ativos:**
   * Os utilizadores ativos podem iniciar sessão diretamente via OAuth
   * Não é necessário convite
   * A conta OAuth é ligada à conta existente deles

## Considerações de segurança

* **Verificação do e-mail:** os fornecedores OAuth têm de fornecer um endereço de e-mail
* **Convite obrigatório:** os novos utilizadores não podem registar-se por conta própria sem um convite
* **Segurança da sessão:** os tokens de convite são guardados de forma segura na sessão
* **Expiração dos tokens:** os tokens de convite expiram após um período configurável (ver `MAX_REGISTRATION_AGE` em [Configurações](settings.md))

## Resolução de problemas

### «Nenhum convite encontrado para este endereço de e-mail»

Este erro ocorre quando:
* O utilizador não clicou numa hiperligação de convite
* O convite expirou
* O e-mail fornecido pelo fornecedor OAuth não corresponde ao e-mail convidado

**Solução:** Peça um novo convite a um administrador com o endereço de e-mail correto.

### «O fornecedor de identidade não forneceu um endereço de e-mail»

Alguns fornecedores OAuth podem não partilhar o endereço de e-mail.

**Solução:** Configure o fornecedor OAuth para incluir o e-mail no scope.

### «Esta conta ainda não está ativa»

A conta do utilizador existe mas ainda não foi ativada.

**Solução:** Utilize a hiperligação de convite enviada por e-mail antes de tentar o início de sessão via OAuth.

## Reinício necessário

Depois de modificar as configurações OAuth no `.env`, reinicie o Cousins Matter:

```bash
docker compose restart
```

## Consulte também

* [Configurações](settings.md) - Referência completa das configurações
* [Instalação](installation.md) - Configuração inicial
* [Funcionalidades](features.md) - Funcionalidades de gestão dos membros
