<div style="display:block; align-items:center">

![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter) ![GitHub Release Date](https://img.shields.io/github/release-date/leolivier/cousins-matter) [![GitHub CI release build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-release.yml/badge.svg)](https://github.com/leolivier/cousins-matter/actions?query=workflow%Release+build) ![GitHub commits since latest release](https://img.shields.io/github/commits-since/leolivier/cousins-matter/latest)

 ![GitHub License](https://img.shields.io/github/license/leolivier/cousins-matter) ![GitHub top language](https://img.shields.io/github/languages/top/leolivier/cousins-matter) [![Django](https://img.shields.io/badge/Django-5.0.2-green)](https://www.djangoproject.com/) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/leolivier/cousins-matter) ![GitHub repo file or directory count](https://img.shields.io/github/directory-file-count/leolivier/cousins-matter) ![GitHub repo size](https://img.shields.io/github/repo-size/leolivier/cousins-matter)

![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-closed-raw/leolivier/cousins-matter) ![GitHub Issues or Pull Requests](https://img.shields.io/github/issues-raw/leolivier/cousins-matter) [![GitHub CI push build status badge](https://github.com/leolivier/cousins-matter/actions/workflows/publish-image-on-push.yml/badge.svg?branch=main)](https://github.com/leolivier/cousins-matter/actions?query=workflow%3APush+build) 

</div>

<table>
 <tr>
  <td width="50%"><img src='https://raw.githubusercontent.com/leolivier/cousins-matter/main/cm_main/static/cm_main/images/cousinades.png' title="Cousins Matter!"></td>
  <td> <h1>Cousins Matter project</h1>
   <p>An application for managing large families, listing all your cousins and allowing them to manage their own profiles.</p>
  </td>
 </tr>
</table>

## Features

## Translations
* Comes with English and French translations
* Can be easily translated into any LTR language, see below. Not tested for RTL.

## Member Management
* Site admin can invite their cousins by email
* Anyone can request an invitation which will be emailed to the site admin who can then invite them. Invitation requests are protected by a captcha.
* Members can create "managed" members, i.e. members who are not active on the site (e.g. for small children or elderly people)
* Managed members can be activated by their managing members (e.g. when a child is old enough to be active on the site).
* Members can be imported in bulk via CSV files
* Member list can be filtered by first and last name
* Members can update their own profile and the profile of the members they manage
* A directory of members can be printed in PDF format
* Birthdays in the next 50 days can be displayed (50 can be changed in settings)

### Galleries
* All active members can create galleries and add photos to them
* Galleries can have sub galleries of any depth
* Photos can be imported in bulk using zip files. Each folder in the zip file becomes a gallery. Updates are managed
* Gallery photo display is paginated

### Settings
Settings can be managed using an .env file (see below).
Many settings are available to customize the site:

#### Security
* SECRET_KEY: A secret key that protects your site. Must be outrageously complex!
* MAX_REGISTRATION_AGE: Maximum validity duration for invitation tokens, default is 2MB

#### General Customization
* SITE_NAME: The name of the site, default is 'Cousins Matter!
* SITE_DOMAIN: The domain of the site, e.g. myfamily.com, no default.
* BIRTHDAY_DAYS: Number of days in the future to display birthdays, default is 50
* HOME_TITLE: The title of your home page.
* HOME_CONTENT_UNSIGNED: The content of the home page displayed to unsigned users. Can contain html tags, but only one line.
* HOME_CONTENT_SIGNED: The content of the home displayed to users who have signed in. Can contain html tags, but only one line.
* HOME_LOGO: Home page logo, the image file must be located in the media/public folder e.g. '/media/public/cousinsmatter.jpg'.
* SITE_COPYRIGHT: Your site copyright, e.g. 'Copyright © 2024 Cousins Matter'.
* PDF_SIZE: PDF page size for the printed directory. 'A4' or 'letter' size
* DEFAULT_GALLERY_PAGE_SIZE: number of photos per gallery page (changeable on screen), default is 25
* MAX_PHOTO_FILE_SIZE: Max size of each photo, default is 5MB
* MAX_GALLERY_BULK_UPLOAD_SIZE: Maximum size of galleries zip bulk upload file, default is 20MB
* MAX_CSV_FILE_SIZE: Maximum size of CSV import file, default is 2MB

#### Log levels
* DJANGO_LOG_LEVEL: Log level for django and internal libraries, default is DEBUG
* CM_LOG_LEVEL: Log level for cousins matter, default is DEBUG

#### Network setup
* ALLOWED_HOSTS: Comma separated list of hosts. The default is '127.0.0.1, localhost'. You MUST set ALLOWED_HOSTS for production!

#### Internationalization
* LANGUAGE_CODE: E.g. 'fr' or 'fr-CA'. Default is 'en-US'.
* TIME_ZONE: Time zone, default is 'Europe/Paris'.

#### Email properties
EMAIL_HOST: SMTP hostname, no default
EMAIL_PORT: Port to connect to on SMTP server
EMAIL_USE_TLS: SMTP server uses STARTLS if true, default is true
EMAIL_USE_SSL: SMTP server uses SSL if true, default is false
EMAIL_HOST_USER: Username to connect to the SMTP server.
EMAIL_HOST_PASSWORD: Password to connect to the SMTP server
DEFAULT_FROM_EMAIL: Default email address to use when sending email

## Coming soon
  * Help/faq/about
  * Posts from all members
  * Classifieds from all members
  * Chat between members
  * Genealogy
  * Color Themes
  * ...
# To install it
* Clone the git repo:
 ```
git clone https://github.com/mariocesar/cousins-matter.git
```
 then cd to the created directory:
 ```
 cd cousins-matter
```	
* To install dependencies:
```
pip install -r requirements.txt
```

> _it's better to do that in a pip env or a conda specific environment_
> ---
* Update your settings:
  Copy `.env.example`to `.env` and edit `.env` to set the properties according to your needs.
* Create your database
  ```
  python manage.py migrate
  ```
  
# To run it
In test/devt mode: 
```
python manage.py runserver
```
In production mode:
```
daphne -b 0.0.0.0 -p 8000 cousinsmatter.asgi:application
```
Then, **only the 1rst time**:
* Create a superuser:
```
python manage.py createsuperuser
```
  and answer the questions, then
* Go to http://127.0.0.1:8000/members/profile
* Login with the superuser account you just created
* Complete your profile
* You're good to go!
* __IMPORTANT__: for production use, you will need to put a reverse proxy in front of the server. It is generally much simpler to use docker for that as everything is pre-installed in the container (see below).
  Otherwise, you can get inspired of what is provided for the docker implementation: instead of running daphne as described above, install lighttpd and run `supervisord -c supervisord.conf` but you'll need some
  simple tweeking of the config files to get it working.

# To update it
 ```
 git pull
 pip install -r requirements.txt
 python manage.py migrate
```
# To generate a new language
```
django-admin makemessages -l <language_code>
```
then edit the different django.po files in the locale folder and finish with:
```
django-admin compilemessages
```
which will compile the translations

# To reset the database completely
Run `./clean_database.sh`

# To use a docker image
* Either build it from source (at the root of the project)
  ```
  docker build -t cousins-matter .
  ```
* Or pull it from ghcr.io
   ```
  docker pull ghcr.io/leolivier/cousins-matter
  ```
  * and create the appropriate directories and cd
    ```
    mkdir -p cousins-matter cousins-matter/data cousins-matter/media && cd cousins-matter
    ```
* Setup your .env configuration
  ```
  curl https://raw.githubusercontent.com/leolivier/cousins-matter/main/.env.example -o .env
  ```
  then edit .env to set the properties according to your context.

# To run with Docker
* run the docker image
```
docker run --name cousins-matter -p 8000:8000 -d -v ./data:/app/data -v ./.env:/app/.env -v ./media:/app/media cousins-matter
```
  Notes:
  1. Replace cousins-matter at the end by `ghcr.io/leolivier/cousins-matter` if you pulled the image from ghcr.io
  2. If you are running on an arm64 platform, don't forget to add the platform option (`--platform linux/arm64`)
  3. Mounted volumes are as follows:
  * `/app/data` must be mounted on a directory where the database will be stored
  * `/app/.env` must be mounted on a file where the environment variables will be stored
  * `/app/media` must be mounted on a directory where the media files will be stored
     
## The first time only
  * Create a superuser:
  ```
  docker exec -it cousins-matter python manage.py createsuperuser
  ```
  and answer the questions, then
  * Go to http://127.0.0.1:8000/members/profile
  * Login with the superuser account you just created
  * Complete your profile
  * **You're good to go!**

# To update with Docker
* Stop the container
```
docker stop cousins-matter
```
* Update the code and rebuild the image
  ```
  git pull
  docker build -t cousins-matter .
```
 or pull the latest image
 ```
  docker pull leolivier/cousins-matter
 ```
* Then rerun it as described above
* And finally, update the database
```
docker exec -it cousins-matter python manage.py migrate
```
* **You're good to go!**

# Todos
* write tests
* develop different subpackages as described above
* manage TLS
* provide tweeked config files for running lighttpd and supervisord outside of docker
