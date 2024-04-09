# Cousins Matter project
Django version with sqlite behind
# To install it
Clone the git repo:
`git clone https://github.com/mariocesar/cousins-matter.git`
then cd to the created directory:
`cd cousins-matter`	
To install dependencies:
`pip install -r requirements.txt`
(it's better to do that in a pip env or a conda specific environment)
Create a superuser:
`python manage.py createsuperuser`
Edit ./cousinsmatter/settings.py to set the properties at the beginning of the file.

# To run it
`python manage.py runserver`
Then, only the 1rst time:
* Go to http://127.0.0.1:8000/
* Login with the superuser account
* Complete your profile (profile menu on the right hand side icon)
* You're good to go

# To generate a new language
`django-admin makemessages -l <language_code>`
then edit the different django.po files in the locale folder
and finish with:
`django-admin compilemessages`	
which will compile the translations

# To reset the database completely
Run `./clean_database.sh`

# To build a docker image
`docker build -t cousins-matter.`	

# To run with Docker
`docker run --name cousinsmatter -p 8000:8000 -d -v ./data:/app/data -v ./.env:/app/.env -v ./media:/app/media cousinsmatter`
then follow the same steps as in the local run section above.


# Todos
* validation signup by admin
* write tests
* create a docker file usable in prod (ie not based on runserver)
* add a footer
* develop different subpackages
  * news
  * classified ads
  * galleries
  * chat
  * genealogy
  * ...