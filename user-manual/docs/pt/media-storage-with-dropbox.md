# AVISO ⚠️ ATUALMENTE APENAS O S3 É SUPORTADO, O DROPBOX NÃO FUNCIONA (provavelmente devido a um problema do django-storages)


# Armazenamento dos média

## AVISOS 

* __Esta é atualmente uma funcionalidade <span class="blinking-text"><u>BETA</u></span>!__
* __Estas configurações são mais complexas e estão <u>reservadas aos utilizadores avançados</u>.__

## Armazenamento dos média predefinido
Por predefinição, os média são armazenados no subdiretório 'media', no mesmo sistema de ficheiros do Cousins Matter.

Isto é muito simples, mas tem alguns inconvenientes, sobretudo em termos de segurança, como explicado em [este artigo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Outros armazenamentos de média

O Cousins Matter também suporta uma série de outros armazenamentos de média através do pacote 'django-storages'. Para configurar tal armazenamento, basta definir duas novas variáveis no seu ficheiro .env: MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS.

Os armazenamentos de média suportados pelo django-storages, na altura em que esta página foi escrita, são: 

* Amazon S3
* Apache Libcloud
* Azure Storage
* Dropbox
* FTP
* Google Cloud Storage
* SFTP
* Compatíveis com S3
	* Backblaze B2
	* Cloudflare R2
	* Digital Ocean
	* Oracle Cloud
	* Scaleway

**Até agora, apenas o armazenamento Dropbox e o armazenamento Cloudflare R2 foram testados e experimentados**, mas todos os outros armazenamentos deverão funcionar, desde que encontre a configuração certa. Consulte [Outros armazenamentos compatíveis com S3](#other-s3-compatible-storages) e [Armazenamentos não testados](#non-tested-storages) abaixo.

Se conseguir criar uma configuração funcional para armazenamentos não testados, crie por favor um Pull Request no GitHub neste ficheiro para explicar como funciona.

### Cloudflare R2

Para utilizar o Cloudflare R2, obviamente precisa primeiro de [criar uma conta no Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Depois, tem de [criar um bucket S3 no Cloudflare R2 - separador Dashboard](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Guarde o nome do bucket.

Também precisa de [criar um token de aplicação](https://developers.cloudflare.com/r2/api/tokens/). Guarde a chave de acesso, a chave secreta e os URLs de endpoint na última página, quando o seu token de API for criado.

Feito isto, a configuração no seu ficheiro .env deverá ter o seguinte aspeto:
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS='{"access_key":"<your access key>","secret_key":"<your secret key>","bucket_name":"<your bucket name>","endpoint_url":"https://<your account id>.r2.cloudflarestorage.com"}'
```
Em seguida, reinicie o Cousins Matter: `docker compose restart cousins-matter`

#### Outros armazenamentos compatíveis com S3

A configuração dos outros armazenamentos compatíveis com S3 (incluindo o AWS S3, o original) deverá ser semelhante à do R2, mas ainda não foi testada.
Como todos estes backends partilham a mesma implementação, não precisa de criar a sua própria imagem, conforme descrito para os [armazenamentos não testados](#non-tested-storages) abaixo.
Consulte a [documentação do django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para saber que variáveis específicas devem ser definidas nas opções para o seu caso particular.

### Dropbox

Precisará de uma conta Dropbox para utilizar este armazenamento (ver https://www.dropbox.com/register).
Depois, terá de [criar uma aplicação](https://www.dropbox.com/developers/apps). O formulário de configurações deverá ter o seguinte aspeto:
![criar aplicação dropbox](assets/create_dropbox_app.webp). Guarde a app key e a app secret.
Vá ao separador Permissions (Permissões) e preencha o formulário assim:
![permissões da aplicação dropbox](assets/dropbox_app_permissions.webp)
Não se esqueça de clicar em Submit (Enviar) no final...

Depois, conforme descrito na [página Dropbox do Django-storages](https://django-storages.readthedocs.io/en/latest/backends/dropbox.html), obtenha o seu código de autorização e, utilizando esse código, obtenha o access_token (que começa por "sl.") e o refresh token.

Feito isto, a configuração no seu ficheiro .env deverá ter o seguinte aspeto:

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS='{"app_key":"<your app key>","app_secret":"<your app secret>","root_path":"/","oauth2_access_token":"<your access token>","oauth2_refresh_token":"<your refresh token>"}'
```

## Armazenamentos não testados

### Instalar o pacote Python necessário

**Nota:** Isto não é necessário para todos os backends compatíveis com S3, consulte acima [Outros armazenamentos compatíveis com S3](#other-s3-compatible-storages)

Primeiro, precisa de instalar um pacote python específico que implemente a ligação ao seu backend. 

Consulte a página relativa ao seu backend na [documentação do django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para saber o nome do seu pacote, que deverá aparecer como `pip install django-storages[<backend name>]`. Guarde o valor de `<backend name>`, pois irá utilizá-lo para o substituir abaixo.

Há duas formas de instalar este pacote; utilize a que lhe parecer melhor...

* Ou cria a sua própria imagem do Cousins Matter derivada da oficial, assim:
	1. crie um Dockerfile desta forma:

		```
		FROM ghcr.io/leolivier/cousins-matter:latest
		RUN pip install django-storages[<backend name>]
		```

	1. compile a nova imagem (mude a etiqueta da imagem como quiser):

		```
		docker build -t cousins-matter:local .
		```

	1. defina COUSINS_MATTER_IMAGE no seu ficheiro .env para se referir a `cousins-matter:local` (ou à sua etiqueta, se a tiver alterado)
	1. recrie os contentores

		```
		docker compose up -d --force-recreate cousins-matter qcluster
		```

	Terá de recompilar a imagem e recriar os contentores cada vez que for lançada uma nova versão.

* Ou atualiza os contentores em execução assim:

	```
	docker exec -it cousins-matter pip install django-storages[<backend name>]
	docker exec -it cousins-matter.qcluster pip install django-storages[<backend name>]
	```

	Terá de executar estes 2 comandos cada vez que os seus contentores forem atualizados com uma nova imagem oficial.

__AVISO__: em alguns casos, há mais do que um pacote a instalar. Por exemplo, se utilizar o Azure Storage com Managed Identity, terá de instalar outro pacote para a Managed Identity. Proceda como descrito acima e acrescente simplesmente os nomes dos outros pacotes no final da linha de comandos `pip install`

### Criar a configuração

Consulte as configurações acima do [Dropbox](#dropbox) e do [Cloudflare R2](#cloudflare-r2) para compreender como funcionam as 2 variáveis MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS, e veja a [documentação do django-storages](https://django-storages.readthedocs.io/en/latest/index.html) do seu backend para adaptar estas configurações ao seu caso.

MEDIA_STORAGE tem de ser retirada da página do seu backend. Utilize o valor de BACKEND no bloco STORAGES (por exemplo, storages.backends.azure_storage.AzureStorage para o backend Azure Storage).

MEDIA_STORAGE_OPTIONS tem de ficar numa única linha. Tem o seguinte formato (a ordem das plicas e das aspas é importante!)

```
MEDIA_STORAGE_OPTIONS='{"option1":"value1","option2":"value2",...}'
```

Substitua option1, option2 pelas variáveis em minúsculas descritas na documentação e pelos respetivos valores para o seu caso.

## Migração do diretório media para um armazenamento externo

__DICA__: se já guardou muitos ficheiros no seu diretório media, a utilização do [rclone](https://rclone.org/install/) poupa-lhe tempo para migrar os seus ficheiros para o novo backend. Crie primeiro uma configuração para o seu backend (`rclone config`) e, em seguida, copie os seus ficheiros de média: `rclone copy ./media <your backend>:<your root>`
