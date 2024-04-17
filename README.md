# Cousins Matter project
An application for managing large families, listing all your cousins and allowing them to manage their own profiles.

Soon to come:
  * help/faq
  * news
  * classified ads
  * galleries
  * chat
  * genealogy
  * ...

# To install it
* Clone the git repo:
 ```
git clone https://github.com/mariocesar/cousins-matter-django.git cousins-matter
```
 then cd to the created directory:
 ```
 cd cousins-matter
```	
* To install dependencies:
```
pip install -r requirements.txt
```
 _(it's better to do that in a pip env or a conda specific environment)_
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
* Or pull it from docker hub
```
docker pull ghcr.io/leolivier/cousins-matter
```
  * and create the appropriate directories and cd
  ```
  mkdir -p cousins-matters cousins-matters/data cousins-matters/media && cd cousins-matters
  ```
* __IMPORTANT__: Download the raw version of the `.env.example` file from https://github.com/leolivier/cousins-matter-django/blob/main/.env.example, rename it to .env and edit it to set the properties according to your context.

# To run with Docker
* run the docker image
```
docker run --name cousins-matter -p 8000:8000 -d -v ./data:/app/data -v ./.env:/app/.env -v ./media:/app/media cousins-matter
```
  (or `ghcr.io/leolivier/cousins-matter` if pulled from docker hub)
  
  Mounted volumes are as follows:
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
