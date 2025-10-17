## Introduction
The settings of Cousins Matter can be managed using a `.env` file in the main directory of the application.

If you have used the docker-install.sh script to install cousins-matter as described in [Installing: the easiest way using Docker](https://github.com/leolivier/cousins-matter/wiki#the-easiest-way-to-run-cousins-matter-docker) , an example .env file has been downloaded for you automatically and the SECRET_KEY has been generated automatically (**don't overwrite it!**).

If you are working from source, copy the `.env.example` file to `.env` 

In both cases, you now need to edit `.env` to set the properties according to your context as described below.

There are many settings available to customize the technical part of your site... 

Also, don't forget to check out [Customization](https://github.com/leolivier/cousins-matter/wiki/Customization) to customize the look and feel of your site.

**WARNING**: If the container is already running, the update of the settings in .env is currently not taken into account until you restart it. 
To do that, it is very simple, just run the following command (in the site directory): `docker compose restart`

## Security
* `SECRET_KEY`: A secret key that protects your site. Must be outrageously complex and kept secret!

  _(Again, if you used docker-install.sh, this has already been generated for you, don't overwrite it)_
* `MAX_REGISTRATION_AGE`: Maximum validity in seconds for invitation tokens, default is 2 days (2*24*3600)

## Superuser
Before running `docker compose up -d` the first time, provide the information to create the superuser (ie the admin account).
* `ADMIN`: the superuser account name
* `ADMIN_PASSWORD`: the superuser password
* `ADMIN_EMAIL`: the superuser email
* `ADMIN_FIRSTNAME`: the superuser first name
* `ADMIN_LASTNAME`: the superuser last name

**ALL THESE VARIABLES ARE MANDATORY TO CREATE THE SUPERUSER ACCOUNT**

If you forgot to provide this information before starting `docker compose up -d`, you can still create it by running 
```
docker exec -it cousins-matter python manage.py createsuperuser
```
It will ask you the parameters interactively.

## Features Management
Since version 1.9.0, you can manage the features that will be offered to members in the .env file.

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
* `MAX_CSV_FILE_SIZE`: Maximum size of CSV member import file, default is 2MB.
### Galleries
* `DEFAULT_GALLERY_PAGE_SIZE`: Number of photos per gallery page (changeable on screen), default is 25
* `MAX_PHOTO_FILE_SIZE`: Maximum size of each photo, default is 5MB
* `MAX_GALLERY_BULK_UPLOAD_SIZE`: Maximum size of galleries zip bulk upload file, default is 20MB
### Messages
* `MESSAGE_MAX_SIZE`: Maximum size of a message in the Forum (note that it may contain a photo), default is 1MB.
* `MESSAGE_COMMENTS_MAX_SIZE`: Maximum size of a comment associated with a message in the Forum, default is 1000

## Log levels
* `DJANGO_LOG_LEVEL`: Log level for django and internal libraries, default is INFO
* `CM_LOG_LEVEL`: Log level for cousins matter, default is INFO

## Network setup
* `ALLOWED_HOSTS`: Comma separated list of hosts. Default is '127.0.0.1, localhost'. __You MUST set ALLOWED_HOSTS for production__ and it __MUST__ contain your full site url and sometimes, depending on your host network settings, the general site IP e.g.:

  `ALLOWED_HOSTS=127.0.0.1,localhost,my.cousins-matter.com,165.157.221.171`

* `CORS_ALLOWED_ORIGINS`: Comma-separated list of hosts. Default is empty. 

  __WARNING!__
  If your log shows errors such as

  `Forbidden (Origin checking failed - https://my.cousins-matter.com/ does not match any trusted origins.): /members/login/`

  you should set `CORS_ALLOWED_ORIGINS=<your full domain>` (e.g. https://my.cousins-matter.com) in the `.env` file, 

  __Don't use the Python syntax shown in the  error!__. 

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
