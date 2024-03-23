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

# To run it
`python manage.py runserver`

# To generate a new language
`django-admin makemessages -l <language_code>`
then edit the different django.po files in the locale folder
and finish with:
`django-admin compilemessages`	
which will compile the translations

# todo
* create a docker file
* develop different subpackages
** news
** classified ads
** galleries
** chat
** ...