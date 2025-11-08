# Media Storage

## WARNINGS 

* __This is currently a <span class="blinking-text"><u>BETA</u></span> feature!__
* __These settings are more complex and are <u>reserved for advanced users</u>.__

## Default media storage
By default, the media are stored in the 'media' sub directory in the same file system as the Cousins Matter.

This is very simple but it has some drawbacks, especially on the security side as explained in [this article](https://security.googleblog.com/2012/08/content-hosting-for-modern-web.html)

## Other media storages

Cousins Matter also supports S3 media storages by using the 'django-storages' package. To setup such a storage, you just need to define two new variables in your .env file: MEDIA_STORAGE and MEDIA_STORAGE_OPTIONS.

**Only the Cloudflare R2 storage has been tested and experimented as of now** but other S3 storages should work as long as you find the right setup. See [Other S3 compatible storages](#other-s3-compatible-storages) below.

If you manage to create a working setup for non tested storages, please create a Pull Request on GitHub on this page to explain how it works.

### Cloudflare R2
To use Cloudflare R2, you obviously first need to [create an account on Cloudflare](https://developers.cloudflare.com/fundamentals/account/create-account/).

Then, you must [create an S3 bucket on Cloudflare R2 - Dashbord tab](https://developers.cloudflare.com/r2/data-catalog/get-started/#1-create-an-r2-bucket). Remember the bucket name.

You also need to [create an application token](https://developers.cloudflare.com/r2/api/tokens/). Remember the access key, secret key and endpoint urls on the last page when your API token is created.

Once this is done, the setup in your .env file should look like this:
```
MEDIA_STORAGE=storages.backends.s3.S3Storage
MEDIA_STORAGE_OPTIONS='{"access_key":"<your access key>","secret_key":"<your secret key>","bucket_name":"<your bucket name>","endpoint_url":"https://<your account id>.r2.cloudflarestorage.com"}'
```
Then restart Cousins Matter: `docker compose restart cousins-matter`

#### Other S3 compatible storages
The setup for other S3 compatible storages (including AWS S3, the original one) should be close to the R2 one but has not yet been tested.
Have a look at [django-storages documentation](https://django-storages.readthedocs.io/en/latest/index.html) to see which specific variables should be set in the options for your particular case.


## Migration from the media directory to an external S3 storage

You can use the S3 storage tools for that. For instance, on AWS S3, you can use
```
$ aws s3 sync ./media s3://YOUR_BUCKET/media/
```

__TIP__: Whatever your S3 provider, using [rclone](https://rclone.org/install/) is a time saver to migrate your files to your new backend. First create a config for your backend (`rclone config`), then copy your media files: `rclone copy ./media <your backend>:<your root>`
