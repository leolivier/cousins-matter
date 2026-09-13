# Armazenamento dos média

## AVISOS 

* __Esta é atualmente uma funcionalidade <span class="blinking-text"><u>BETA</u></span>!__
* __Estas configurações são mais complexas e estão <u>reservadas aos utilizadores avançados</u>.__

## Armazenamento dos média predefinido

Por predefinição, os média são armazenados no subdiretório 'media', no mesmo sistema de ficheiros do Cousins Matter.

Isto é muito simples, mas tem alguns inconvenientes, sobretudo em termos de segurança, como explicado em [este artigo](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Outros armazenamentos de média

O Cousins Matter também suporta armazenamentos de média S3 através do pacote 'django-storages'. Para configurar tal armazenamento, basta definir duas novas variáveis no seu ficheiro .env: MEDIA_STORAGE e MEDIA_STORAGE_OPTIONS.

**Até agora, apenas o armazenamento Cloudflare R2 foi testado e experimentado**, mas os outros armazenamentos S3 deverão funcionar, desde que encontre a configuração certa. Consulte [Outros armazenamentos compatíveis com S3](#other-s3-compatible-storages) abaixo.

Se conseguir criar uma configuração funcional para armazenamentos não testados, crie por favor um Pull Request no GitHub nesta página para explicar como funciona.

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

Consulte a [documentação do django-storages](https://django-storages.readthedocs.io/en/latest/index.html) para saber que variáveis específicas devem ser definidas nas opções para o seu caso particular.


## Migração do diretório media para um armazenamento S3 externo

Pode utilizar as ferramentas do armazenamento S3 para isso. Por exemplo, no AWS S3, pode utilizar

```
$ aws s3 sync ./media s3://YOUR_BUCKET/media/
```

__DICA__: Seja qual for o seu fornecedor S3, a utilização do [rclone](https://rclone.org/install/) poupa-lhe tempo para migrar os seus ficheiros para o novo backend. Crie primeiro uma configuração para o seu backend (`rclone config`) e, em seguida, copie os seus ficheiros de média: `rclone copy ./media <your backend>:<your root>`
