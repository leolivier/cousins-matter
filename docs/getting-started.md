# Getting started with Cousins Matter

## Install Cousins Matter

This has been tested on Linux and Windows+WSL2 with Ubuntu or Debian + Docker Desktop installed. (The install script has not yet been tested on MacOS, but should work with very few changes)

### Install Docker
If not already done, install Docker on your server:
```
curl https://get.docker.com | sh
```

### Download the Cousins Matter admin script then run it
Please replace in the link below the <release\> placeholder with the current release of Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.sh
chmod +x manage_cousins_matter.sh
```

Run the script like this:

```
./manage_cousins_matter.sh install [-d <directory>] [-r <release>]
```

  * if -d directory is not given, it will install in the current directory
  * if -r release is not given, it will install the latest release

This command will:

* download the necessary files for Cousins Matter;
* create the necessary directories;
* create the base .env file from an example;
* run an editor on the .env file to suit your needs (see the [Settings](settings.md) page). In particular, don't forget to add the information to create the superuser.

This script can also help you to [migrate from v1 to v2 version of Cousins Matter](migrate-from-v1-to-v2.md) and to [rotate your secret key from time to time](#rotate-your-secret-key).

To get the different commands available, run:

```
./manage_cousins_matter.sh -h
```

To get help for a specific command, run:

```
./manage_cousins_matter.sh <command> -h
```

### Start Cousins Matter

```
cd <directory>
docker compose up -d
```

__The first time__, go to http://127.0.0.1:8000/members/profile, log in using the admin account that you have just created and complete your profile.

**And you're done!**

## Build from source

* Install Docker

```
curl https://get.docker.com | sh
```

* Clone the git repo:

```
git clone https://github.com/mariocesar/cousins-matter.git
cd cousins-matter
```

* Install the dependencies:

```
pip install -r requirements.txt
```

> __It is advised to do this in a virtual environment (using pip env, uv or conda).__

* Update your settings:
  Copy `.env.example` to `.env` and edit `.env` to set the properties according to your needs, see the [Settings](settings.md) page.
  You can automatically create the SECRET_KEY by running the following command:

```
./manage_cousins_matter.sh rotate-secrets
```

* build the docker image:

```
docker build -t cousins-matter:local .
```

* Update the docker-compose.yml file to use the local image by adding the following line to the .env file:
```
COUSINS_MATTER_IMAGE=cousins-matter:local
```

* Start everything:

```
docker compose up -d
```
 
### Run it outside Docker

if you want to debug your installation, you can run it outside Docker.

For this, you'll need to start postgresql and redis using the docker-compose.yml file:

```
docker compose up -d postgres redis
```

To allow the app to use redis and postgres, you'll need to set the following environment variables:

```
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
```

Then, run the following commands:
```
python manage.py runserver
```

or start debugging from your IDE (the project is already configured for Visual Studio Code in the .vscode/launch.json file)

## Upgrade
### Docker
Pull the latest image and restart the container
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### From source
Refresh sources from github, reinstall packages, migrate the database
```
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Migrate from Version 1 to Version 2
The version 2 of Cousins Matter is a big rewrite of the version 1 and is not directly compatible with the version 1. 
Amongst other big changes:

* the database has been migrated from sqlite3 to postgresql to allow for better performance and scalability.
* cousins matter is now composed of at least 4 docker containers:

    * the web server
    * the database
    * redis
    * the asynchronous tasks server

To migrate from version 1 to version 2, please follow the instructions in the [migrate from v1 to v2 version of Cousins Matter](migrate-from-v1-to-v2.md) page.

## Rotate your secret key
From time to time (e.g. once a month), you should rotate the Cousins Matter secret key. To do so, run the following command:

```
./manage_cousins_matter.sh rotate-secrets
```

This command will rotate the secret key and update the PREVIOUS_SECRET_KEYS in the .env file.

As Cousins Matter cannot change itself its secret key, you will need to restart the Cousins Matter containers to apply the new secret key.

To do so, run the following command:

```
docker compose up -d --force-recreate
```
