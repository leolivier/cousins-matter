# Getting started with Cousins Matter

## The easiest way to run Cousins Matter: Docker

This has been tested on Linux and Windows+WSL2 with Ubuntu or Debian + Docker Desktop installed. (The install script has not yet been tested on MacOS, but should work with very few changes)

* Install cousins-matter:

  The following command will install cousins-matter **in the current directory**:

  ![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=replace%20%3Crelease%3E%20below%20by%3A&labelColor=%23f00&color=%23ffff)
   ```shell
   curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/docker-install.sh | bash
   ```
   Then edit the generated `.env` file to suit your needs (see the [Settings](wiki/settings) page). In particular, don't forget to add the information to create the superuser.

* Run cousins-matter:
  ```shell
  $ docker compose up -d
  ```
  __The first time__, go to http://127.0.0.1:8000/members/profile, log in with the superuser account you just created, and fill out your profile

  **And you're done!**

## Install from source
* Clone the git repo:
  ```
  git clone https://github.com/mariocesar/cousins-matter.git
  ```
* Then cd to the created directory:
   ```
   cd cousins-matter
  ```	
* Install the dependencies:
  ```
  pip install -r requirements.txt
  ```

  > __It is better to do this in a pip env or a conda specific environment__.

* Update your settings:
  Copy `.env.example` to `.env` and edit `.env` to set the properties according to your needs, see the [Settings](wiki/settings) page.
* Create your database
  ```
  python manage.py migrate
  ```
* To get the chat working, you'll need to install redis open source (see [install redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)) and then run it with the default configuration (just run `redis-server`)

* In a terminal, to start the django cluster which will run the asynchronous tasks, run
  ```
  python manage.py qcluster
  ```

* Finally, in another terminal, run:
  ```
  python manage.py runserver
  ```
 
## Run it from source
* In test/devt mode: 
  ```
  python manage.py runserver
  ```
* In production mode:
  ```
  daphne -b 0.0.0.0 -p 8000 cousinsmatter.asgi:application
  ```
* Then, **only the first time**:
  * Create a superuser:
  ```
  python manage.py createsuperuser
  ```
  and answer the questions, then
  * Go to http://127.0.0.1:8000/members/profile
  * Log in with the superuser account you just created
  * Fill out your profile
  * You're good to go!

### IMPORTANT
For real production use and good management of static and media files, you will need to put a reverse proxy in front of the server. It is generally much easier to use Docker for this as everything comes preinstalled in the container (see above).
If you want to run from source without Docker, instead of running `daphne`, download [lighttpd](https://www.lighttpd.net/), and run `./scripts/manual-start.sh` from the project directory. 

__WARNING:__ At the time of writing, there is an issue with socket creation, that prevents this solution from working, see issue #53. Since the Docker solution is preferred, there is currently no rush to fix this bug, but feel free to do so and open a PR ;)


## Upgrade
### Docker
Pull the latest image and restart the container
```
cd cousins-matter
docker compose pull
docker compose up -d --force-recreate
```

### From source
Refresh sources from github, reinstall packages, migrate the database
```
git pull
pip install -r requirements.txt
python manage.py migrate
```
then restart the daemon

## Other possible actions
### Translate to a new language
```
python manage.py makemessages -l <language_code>
```
then edit the different django.po files in the locale folders and finish with:
```
python manage.py compilemessages
```
which will compile the translations

### Build docker image from the sources
  ```
  docker build -t cousins-matter:local .
  ```
To start this image:
  ```
  COUSINS_MATTER_IMAGE=cousins-matter:local docker compose up -d --force-recreate
  ```