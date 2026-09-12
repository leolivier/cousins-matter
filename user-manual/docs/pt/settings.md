# Configurações

## Introdução

As configurações do Cousins Matter podem ser geridas através de um ficheiro `.env` no diretório principal da aplicação.

Se utilizou o script manage_cousins_matter.py para instalar o Cousins Matter, conforme descrito em [Instalação](installation.md), um ficheiro .env de exemplo foi descarregado automaticamente para si e a SECRET_KEY e a POSTGRES_PASSWORD foram geradas automaticamente (**não as substitua!**).

Se está a trabalhar a partir do código-fonte, copie o ficheiro `.env.example` para `.env` 

Em ambos os casos, agora precisa de editar o `.env` para definir as propriedades conforme o seu contexto, como descrito abaixo.

Há muitas configurações disponíveis para personalizar a parte técnica do seu sítio... 

Além disso, não se esqueça de consultar [Personalização](customizing.md) para personalizar a aparência do seu sítio.

**AVISO**: Se o contentor já estiver em execução, a atualização das configurações no .env só será tida em conta depois de o reiniciar. 
Para isso, basta executar o seguinte comando (no diretório do sítio): 
```
docker compose restart
```

## Segurança

* `SECRET_KEY`: Uma chave secreta que protege o seu sítio. Tem de ser absurdamente complexa e mantida em segredo! A forma mais fácil de a gerar é executar `python manage_cousins_matter.py rotate-secrets`. Este script também atualizará a PREVIOUS_SECRET_KEYS no ficheiro .env. Esta variável é utilizada para descodificar os tokens que foram enviados aos membros com a chave secreta anterior.

	_(Mais uma vez, se utilizou o manage_cousins_matter.py para instalar o Cousins Matter, isto já foi gerado para si, não o substitua)_
* `MAX_REGISTRATION_AGE`: Validade máxima, em segundos, dos tokens de convite; por predefinição, 2 dias (2*24*3600)

## Superutilizador

Antes de executar `docker compose up -d` pela primeira vez, indique as informações para criar o superutilizador (ou seja, a conta de administrador).

* `ADMIN`: o nome da conta do superutilizador
* `ADMIN_PASSWORD`: a palavra-passe do superutilizador
* `ADMIN_EMAIL`: o e-mail do superutilizador
* `ADMIN_FIRSTNAME`: o nome próprio do superutilizador
* `ADMIN_LASTNAME`: o apelido do superutilizador

**TODAS ESTAS VARIÁVEIS SÃO OBRIGATÓRIAS PARA CRIAR A CONTA DO SUPERUTILIZADOR E NÃO TÊM VALORES PREDEFINIDOS**

## Gestão das funcionalidades

Pode gerir, no ficheiro .env, as funcionalidades que serão oferecidas aos membros.

Para isso, modifique a variável FEATURES_FLAGS com base no conteúdo do ficheiro .env.example e defina como false o valor de cada funcionalidade a ignorar.

O valor predefinido de FEATURES_FLAGS é:
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True;show_public_chats=True;show_private_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_site_stats=True;show_export_members=True;show_change_language=True;show_genealogy=True"
```

**Bandeiras de funcionalidades disponíveis:**

* `show_birthdays_in_homepage`: Apresenta os próximos aniversários na página inicial dos membros autenticados
* `show_galleries`: Ativa a funcionalidade de galerias de fotos e vídeos
* `show_forums`: Ativa os debates no fórum
* `show_public_chats`: Ativa as salas de conversa públicas
* `show_private_chats`: Ativa as salas de conversa privadas
* `show_classified_ads`: Ativa a funcionalidade de anúncios classificados
* `show_polls`: Ativa a funcionalidade de sondagens
* `show_event_planners`: Ativa os inquéritos de planeamento de eventos (sondagens de escolha de datas)
* `show_pages`: Ativa a funcionalidade de páginas CMS
* `show_treasures`: Ativa a funcionalidade de tesouros (tesouros de família)
* `show_site_stats`: Mostra a página de estatísticas do sítio
* `show_export_members`: Permite a exportação do diretório de membros em PDF
* `show_change_language`: Permite a mudança de idioma na interface
* `show_genealogy`: Ativa as funcionalidades de genealogia (árvores de família, importação/exportação GEDCOM)

**AVISOS:**

1. A variável INCLUDE_BIRTHDAYS_IN_HOMEPAGE foi substituída pela bandeira de funcionalidade show_birthdays_in_homepage, como mostrado acima.
2. A FEATURES_FLAGS tem de ficar numa única linha no ficheiro .env. Todas as bandeiras são separadas por ponto e vírgula. Se definir esta variável no seu ficheiro .env e uma bandeira não estiver presente na lista, é considerada false.

## Personalização geral

### Sítio

* `SITE_NAME`: O nome do sítio; por predefinição, 'Cousins Matter!'.
* `SITE_DOMAIN`: O domínio do sítio, por exemplo, myfamily.com; sem valor predefinido.
* `SITE_FOOTER`: O rodapé opcional do sítio, por exemplo, "The Simpsons Family Social Network".
* `SITE_LOGO`: O URL relativo opcional do logótipo do seu sítio (no canto superior esquerdo). Deve ter uma proporção de 4:1. **TEM DE SER GUARDADO NA** pasta media/public do seu sítio, pelo que **o URL tem de começar por '/media/public'** (por exemplo, SITE_LOGO='/media/public/my-own-logo.jpg')
* `SITE_COPYRIGHT`: O copyright do seu sítio, por exemplo, 'Copyright © 2024 Cousins Matter'.
* `DARK_MODE`: Ativa o tema do modo escuro. Por predefinição, False.

### Membros

* `ALLOW_MEMBERS_TO_CREATE_MEMBERS`: Por predefinição, True. Para impedir que os membros criem e gerem outros membros, defina como False e apenas os administradores o poderão fazer.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS`: Por predefinição, True. Para impedir que os membros convidem outros membros a juntar-se ao sítio, defina como False e apenas os administradores o poderão fazer.
* `BIRTHDAY_DAYS`: Número de dias no futuro para apresentar os aniversários; por predefinição, 50
* ~~`INCLUDE_BIRTHDAYS_IN_HOMEPAGE`~~: **OBSOLETO** - Utilize antes `show_birthdays_in_homepage` em `FEATURES_FLAGS`
* `PDF_SIZE`: Tamanho da página PDF do diretório impresso. Formato 'A4' ou 'letter'. Por predefinição, A4.
* `MAX_CSV_FILE_SIZE`(*): Tamanho máximo do ficheiro CSV de importação de membros; por predefinição, 2MB.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP`: Indique aqui o IP externo do seu servidor. É utilizado para o rastreio dos inícios de sessão quando estes provêm da rede interna. Por predefinição, "8.8.8.8".
* `LOGIN_HISTORY_PURGE_DAYS`: Número de dias durante os quais se mantém o histórico de inícios de sessão (visível para os administradores no admin do Django); por predefinição, 365.

### Galerias

* `DEFAULT_GALLERY_PAGE_SIZE`: Número de fotos por página de galeria (alterável no ecrã); por predefinição, 25
* `MAX_PHOTO_FILE_SIZE`(*): Tamanho máximo de cada foto; por predefinição, 5MB
* `MAX_VIDEO_FILE_SIZE`(*): Tamanho máximo de cada vídeo; por predefinição, 20MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): Tamanho máximo do ficheiro zip de carregamento em massa de galerias; por predefinição, 20MB
* `SLIDESHOW_DELAY`: Intervalo, em segundos, entre cada foto numa apresentação de diapositivos; por predefinição, 5

### Mensagens e conversas

* `MESSAGE_MAX_SIZE`(*): Tamanho máximo de uma mensagem no Fórum ou nas conversas (note que pode conter uma foto); por predefinição, 2.5MB.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): Tamanho máximo de um comentário associado a uma mensagem no Fórum ou nas conversas; por predefinição, 1000
* `CONTACT_MAX_SIZE`(*): Tamanho máximo de uma mensagem de contacto; por predefinição, 1MB

### Páginas

* `PAGE_MAX_SIZE`(*): Tamanho máximo de uma página simples; por predefinição, 10MB

### Sondagens

* `POLL_MAX_SIZE`(*): Tamanho máximo de uma sondagem; por predefinição, 1MB

### Anúncios classificados

* `CLASSIFIED_AD_MAX_SIZE`(*): Tamanho máximo de um anúncio classificado; por predefinição, 1MB

### Tesouros

* `TROVE_FILE_MAX_SIZE`(*): Tamanho máximo de um ficheiro de tesouro; por predefinição, 20MB
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): Tamanho máximo de uma imagem de tesouro; por predefinição, 5MB
* `TROVE_THUMBNAIL_SIZE`(*): Tamanho máximo, em píxeis, de uma miniatura de tesouro; por predefinição, 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): Número predefinido de tesouros por página; por predefinição, 10

### Anúncios classificados

* `MAX_PHOTO_PER_AD`: Número máximo de fotos por anúncio classificado; por predefinição, 10

### Genealogia

* `FAMILY_CHART_GENERATIONS`: Número de gerações a mostrar para cima e para baixo a partir da pessoa central no gráfico de família; por predefinição, 4
* `FAMILY_CHART_ROOT_PERSON_ID`: ID da pessoa raiz predefinida a mostrar no gráfico de família se nenhum for especificado; por predefinição, o id da primeira pessoa na base de dados
* `GEDCOM_FILE`: Ficheiro GEDCOM a utilizar para exportar a genealogia; por predefinição, 'genealogy.ged'

## Autenticação OAuth/SSO

* `OAUTH_PROVIDERS`: Lista separada por vírgulas dos fornecedores OAuth a ativar. Fornecedores disponíveis: `google`, `facebook`, `apple`, `github`, `pocketid`, ou qualquer fornecedor `openid_connect`. Por predefinição, vazio (sem OAuth ativado).
* `SOCIALACCOUNT_AUTO_SIGNUP`: Se é exigida uma confirmação quando um utilizador inicia sessão com um fornecedor OAuth. Por predefinição, False (confirmação exigida).

Para cada fornecedor, precisa de definir:
* `<PROVIDER>_OAUTH_CLIENT_ID`: O client ID OAuth do fornecedor
* `<PROVIDER>_OAUTH_CLIENT_SECRET`: O client secret OAuth do fornecedor

Para os fornecedores de OpenID Connect (incluindo o PocketID):
* `<PROVIDER>_SERVER_URL`: URL do servidor de OpenID Connect

**Exemplo de configuração:**
```
OAUTH_PROVIDERS=google,github,pocketid
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

Consulte [Autenticação OAuth](oauth-authentication.md) para obter instruções de configuração detalhadas de cada fornecedor.

## Níveis de registo (log)

* `DJANGO_LOG_LEVEL`: Nível de registo para o django e as bibliotecas internas; por predefinição, INFO
* `CM_LOG_LEVEL`: Nível de registo para o cousins matter; por predefinição, INFO

## Configuração de rede

* `ALLOWED_HOSTS`: Lista de anfitriões separada por vírgulas. Por predefinição, '127.0.0.1,localhost,<SITE_DOMAIN\>'. __Tem de definir ALLOWED_HOSTS em produção__ e ele __TEM DE__ conter o URL completo do seu sítio e, por vezes, dependendo das configurações de rede do seu anfitrião, o IP geral do sítio, por exemplo:

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: Lista de anfitriões separada por vírgulas. Por predefinição, vazio. 

	__AVISO!__ Se o seu registo mostrar erros como

	`Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

	deve definir `CORS_ALLOWED_ORIGINS=<your full domain>` (por exemplo, https://my.cousins-matter.com) no ficheiro `.env`, 

	__Não utilize a sintaxe Python mostrada no erro!__. 

	Se tiver vários anfitriões, liste-os separados por vírgulas, por exemplo

	`CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

	Para informação, `CSRF_TRUSTED_ORIGINS` é definido com o valor de `CORS_ALLOWED_ORIGINS`

## Internacionalização

* `LANGUAGE_CODE`: Por exemplo, 'pt' ou 'pt-PT'. Por predefinição, 'en-US'.
* `TIME_ZONE`: Fuso horário; por predefinição, 'Europe/Paris'.

## Propriedades de e-mail

* `EMAIL_HOST`: Nome do anfitrião SMTP, sem valor predefinido
* `EMAIL_PORT`: Porta à qual ligar no servidor SMTP
* `EMAIL_USE_TLS`: O servidor SMTP utiliza STARTLS se verdadeiro; por predefinição, true
* `EMAIL_USE_SSL`: O servidor SMTP utiliza SSL se verdadeiro; por predefinição, false
* `EMAIL_HOST_USER`: Nome de utilizador para ligar ao servidor SMTP.
* `EMAIL_HOST_PASSWORD`: Palavra-passe para ligar ao servidor SMTP
* `DEFAULT_FROM_EMAIL`: Endereço de e-mail predefinido a utilizar no envio de e-mails

## Base de dados

* `POSTGRES_USER`: O utilizador postgres; por predefinição, 'cousinsmatter'
* `POSTGRES_PASSWORD`: A palavra-passe do postgres. É gerada automaticamente se utilizar o manage_cousins_matter.py para instalar ou migrar o Cousins Matter. __AVISO!__ Utilize apenas -_./* como caracteres especiais se quiser alterá-la. Evite absolutamente : e @ !
* `POSTGRES_DB`: A base de dados postgres; por predefinição, 'cousinsmatter'
* `POSTGRES_HOST`: O anfitrião postgres; por predefinição, 'postgres'

* `REDIS_HOST`: O anfitrião redis; por predefinição, 'redis'

## Outros armazenamentos de média

* `MEDIA_STORAGE` e `MEDIA_STORAGE_OPTIONS`: Consulte [Armazenamento dos média](/media-storage.md)

## NOTAS

__(*) AVISO:__ Se quiser alterar qualquer uma das variáveis que controlam o tamanho daquilo que pode ser carregado e estiver a utilizar o proxy inverso nginx, verifique que o valor de `client_max_body_size` em config/nginx/nginx.conf se mantém superior às variáveis de tamanho que alterar acima. Caso contrário, receberá um erro 413 do Nginx. O valor predefinido fornecido é elevado (20MB), mas pode ter de o aumentar para suportar vídeos maiores.
