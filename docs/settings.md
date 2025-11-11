# Settings

## Introduction
The settings of Cousins Matter can be managed using a `.env` file in the main directory of the application.

If you have used the manage_cousins_matter.py script to install Cousins Matter as described in [Installation](installation.md), an example .env file has been downloaded for you automatically and the SECRET_KEY and the POSTGRES_PASSWORD have been generated automatically (**don't overwrite them!**).

If you are working from source, copy the `.env.example` file to `.env` 

In both cases, you now need to edit `.env` to set the properties according to your context as described below.

There are many settings available to customize the technical part of your site... 

Also, don't forget to check out [Customization](customizing.md) to customize the look and feel of your site.

**WARNING**: If the container is already running, the update of the settings in .env won't be taken into account until you restart it. 
To do that, just run the following command (in the site directory): 
```
docker compose restart
```

## Security
* `SECRET_KEY`: A secret key that protects your site. Must be outrageously complex and kept secret! The easiest way to generate it is to run `python manage_cousins_matter.py rotate-secrets`. This script will also update the PREVIOUS_SECRET_KEYS in the .env file. This variable is used to decode the tokens that have been sent to members with the previous secret key.

	_(Again, if you used manage_cousins_matter.py to install Cousins Matter, this has already been generated for you, don't overwrite it)_
* `MAX_REGISTRATION_AGE`: Maximum validity in seconds for invitation tokens, default is 2 days (2*24*3600)

## Superuser
Before running `docker compose up -d` the first time, provide the information to create the superuser (ie the admin account).
* `ADMIN`: the superuser account name
* `ADMIN_PASSWORD`: the superuser password
* `ADMIN_EMAIL`: the superuser email
* `ADMIN_FIRSTNAME`: the superuser first name
* `ADMIN_LASTNAME`: the superuser last name

**ALL THESE VARIABLES ARE MANDATORY TO CREATE THE SUPERUSER ACCOUNT AND HAVE NO DEFAULT VALUES**

If you forgot to provide this information before starting `docker compose up -d`, you can still create it by running 
```
docker exec -it cousins-matter python manage.py createsuperuser
```
It will ask you the parameters interactively.

## Features Management
You can manage the features that will be offered to members in the .env file.

To do so, modify the FEATURES_FLAGS variable based on the contents of the .env.example file and set the value of each feature to be ignored to false.

The default value of FEATURES_FLAGS is:
```
FEATURES_FLAGS="show_birthdays_in_homepage=True;show_galleries=True;show_forums=True;show_chats=True;show_classified_ads=True;show_polls=True;show_event_planners=True;show_pages=True;show_treasures=True;show_privacy_policy=True;show_site_stats=True;show_import_members=True;show_export_members=True"`
```
**WARNINGS:**
1. The variable INCLUDE_BIRTHDAYS_IN_HOMEPAGE has been replaced by the feature flag show_birthdays_in_homepage, as shown above.
2. The FEATURES_FLAGS must stay on one line in the .env file. All flags are separated by semicolons. If you set this variable in your .env file and a flag is not present in the list, it is considered false.

## General Customization
### Site
* `SITE_NAME`: The name of the site, default is 'Cousins Matter!'.
* `SITE_DOMAIN`: The domain of the site, e.g. myfamily.com, no default.
* `SITE_FOOTER`: The optional footer of the site, e.g. "The Simpsons Family Social Network".
* `SITE_LOGO`: The optional relative URL of your site logo (in the top left corner). Must have a 4:1 ratio. **MUST BE STORED IN** your site's media/public folder, so **the URL must start with '/media/public'** (e.g. SITE_LOGO='/media/public/my-own-logo.jpg')
* `SITE_COPYRIGHT`: Your site copyright, e.g. 'Copyright © 2024 Cousins Matter'.
### Members
* `ALLOW_MEMBERS_TO_CREATE_MEMBERS`: Default is True. To prevent members from creating and managing other members, set to False and only admins will be able to do this.
* `ALLOW_MEMBERS_TO_INVITE_MEMBERS`: Default is True. To prevent members from inviting other members to join the site, set to False and only admins will be able to do this.
* `BIRTHDAY_DAYS`: Number of days in the future to display birthdays, default is 50
* `INCLUDE_BIRTHDAYS_IN_HOMEPAGE`: Should birthdays be included in the homepage for authenticated members? Default is True
* `PDF_SIZE`: PDF page size for printed directory. 'A4' or 'letter' size. Default is A4.
* `MAX_CSV_FILE_SIZE`(*): Maximum size of CSV member import file, default is 2MB.
* `LOGIN_HISTORY_GEOLOCATION_PLACEHOLDER_IP`: Enter here the external IP of your server. It is used for the login trace when the login comes from the internal network. Default is "8.8.8.8".
* `LOGIN_HISTORY_PURGE_DAYS`: Number of days to keep login history, default is 365.
### Galleries
* `DEFAULT_GALLERY_PAGE_SIZE`: Number of photos per gallery page (changeable on screen), default is 25
* `MAX_PHOTO_FILE_SIZE`(*): Maximum size of each photo, default is 5MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`(*): Maximum size of galleries zip bulk upload file, default is 20MB
### Messages and chats
* `MESSAGE_MAX_SIZE`(*): Maximum size of a message in the Forum or in the chats (note that it may contain a photo), default is 2.5MB.
* `MESSAGE_COMMENTS_MAX_SIZE`(*): Maximum size of a comment associated with a message in the Forum or in the chats, default is 1000
* `CONTACT_MAX_SIZE`(*): Maximum size of a contact message, default is 1MB
### Pages
* `PAGE_MAX_SIZE`(*): Maximum size of a flat page, default is 10MB
### Polls
* `POLL_MAX_SIZE`(*): Maximum size of a poll, default is 1MB
### Classified ads
* `CLASSIFIED_AD_MAX_SIZE`(*): Maximum size of a classified ad, default is 1MB
### Troves
* `TROVE_FILE_MAX_SIZE`(*): Maximum size of a trove file, default is 20MB
* `TROVE_PICTURE_FILE_MAX_SIZE`(*): Maximum size of a trove picture, default is 5MB
* `TROVE_THUMBNAIL_SIZE`(*): Maximum size of a trove thumbnail in pixels, default is 100
* `DEFAULT_TROVE_PAGE_SIZE`(*): Default number of troves per page, default is 10
### Classified ads
* `MAX_PHOTO_PER_AD`: Maximum number of photos per classified ad, default is 10

## Log levels
* `DJANGO_LOG_LEVEL`: Log level for django and internal libraries, default is INFO
* `CM_LOG_LEVEL`: Log level for cousins matter, default is INFO

## Network setup
* `ALLOWED_HOSTS`: Comma separated list of hosts. Default is '127.0.0.1,localhost,<SITE_DOMAIN\>'. __You MUST set ALLOWED_HOSTS for production__ and it __MUST__ contain your full site url and sometimes, depending on your host network settings, the general site IP e.g.:

	`ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: Comma-separated list of hosts. Default is empty. 

	__WARNING!__
	If your log shows errors such as

	`Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

	you should set `CORS_ALLOWED_ORIGINS=<your full domain>` (e.g. https://my.cousins-matter.com) in the `.env` file, 

	__Don't use the Python syntax shown in the error!__. 

	If you have multiple hosts, list them separated by commas, e.g.

	`CORS_ALLOWED_ORIGINS=https://my.cousins-matter.com,https://my.cousins-matter.org`

	For information, `CSRF_TRUSTED_ORIGINS` is set to the value of `CORS_ALLOWED_ORIGINS`

## Internationalization
* `LANGUAGE_CODE`: E.g. 'fr' or 'fr-CA'. Default is 'en-US'.
* `TIME_ZONE`: Time zone, default is 'Europe/Paris'.

## Email properties
* `EMAIL_HOST`: SMTP host name, no default
* `EMAIL_PORT`: Port to connect to on SMTP server
* `EMAIL_USE_TLS`: SMTP server uses STARTLS if true, default is true
* `EMAIL_USE_SSL`: SMTP server uses SSL if true, default is false
* `EMAIL_HOST_USER`: User name to connect to the SMTP server.
* `EMAIL_HOST_PASSWORD`: Password for connecting to the SMTP server
* `DEFAULT_FROM_EMAIL`: Default email address to use when sending email

## Database
* `POSTGRES_USER`: The postgres user, default is 'cousinsmatter'
* `POSTGRES_PASSWORD`: The postgres password. It is generated automatically if you use manage_cousins_matter.py to install or migrate Cousins Matter. __WARNING!__ Use only -_./* as special characters if you want to change it. Absolutely avoid : and @ !
* `POSTGRES_DB`: The postgres database, default is 'cousinsmatter'
* `POSTGRES_HOST`: The postgres host, default is 'postgres'

* `REDIS_HOST`: The redis host, default is 'redis'

## Other media storage
* `MEDIA_STORAGE` and `MEDIA_STORAGE_OPTIONS`: See [Media Storage](/media-storage.md)

## NOTES
__(*) WARNING:__ If you want to change any of the variables controling the size of what can be uploaded and you are using the nginx reverse proxy, please check that the value of `client_max_body_size` in config/nginx.conf so that it remains higher than the size variables you change above. Otherwise you will receive a 413 error from Nginx. The default value provided is high (20MB) so it should be an issue except when videos is supported.
