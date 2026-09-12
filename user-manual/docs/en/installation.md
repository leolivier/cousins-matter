# Installation of Cousins Matter

This has been tested on Linux and Windows+WSL2 with Ubuntu or Debian + Docker Desktop installed. (The install script has not yet been tested on MacOS, but should work with very few changes)

## Production installation

### Prerequisites

If not already done, install Docker on your server:
```
curl https://get.docker.com | sh
```

You will also need a Python 3.14+ environment to run the Cousins Matter admin script.

### Download and run the Cousins Matter admin script

Please replace in the link below the **<release\>** placeholder with the current release of Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <directory>] [-r <release>]
```

* if -d directory is not given, it will install in the current directory
* if -r release is not given, it will install the latest release

This command will:

* download the necessary files for Cousins Matter;
* create the necessary directories;
* create the base .env file from an example;
* run an editor on the .env file to suit your needs (see the [Settings](settings.md) page). In particular, __don't forget to add the information to create the superuser__.

This script can also help you to [migrate from v1 to v2 version of Cousins Matter](migrate-from-v1-to-v2.md) and to [rotate your secret key from time to time](other-management-operations.md#rotate-your-secret-key).

To get the different commands available, run:

```
python manage_cousins_matter.py -h
```

To get help for a specific command, run:
```
python manage_cousins_matter.py <command> -h
```

### Start Cousins Matter

```
cd <directory>
docker compose up -d
```

__The first time__, go to http://127.0.0.1:8000/members/profile, log in using the admin account that you have just created and complete your profile.

**And you're done!**

## Build from source

* Install Docker and uv if not yet done

	```
	curl https://get.docker.com | sh
  pip install uv
	```

* Clone the git repo:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

**Note for contributors:** if you want to contribute to the cousins-matter development, first fork the project on github and clone your own repo.

* Create and sync your python virtual environment:
  ```
  uv sync
	```

* Update your settings:
	Copy `.env.example` to `.env` and edit `.env` to set the properties according to your needs, see the [Settings](settings.md) page.

	You can automatically create the SECRET_KEY by running the following command:

	```
	./manage_cousins_matter.sh rotate-secrets
	```

* build the docker image:

	```
	make build t=cousins-matter:local
	```

* Use your local image by adding the following line to the .env file:
	```
	COUSINS_MATTER_IMAGE=cousins-matter:local
	```

* Start everything:

	```
	make up
	```

### Run it outside Docker

If you want to debug your installation, you can run it outside Docker.

For this, instead of starting `make up`, use:
```
make up4run  # will start the needed containers: postgres, redis, and qcluster (using the image built previously)
# to start cousins-matter in dev mode
make run  # will reload automatically after each code modification
# to run tests (no UI tests)
make test [t=<test name>]
# to run UI tests
make test-ui [t=<test name>]
# get all other make command by just running
make
```
or start debugging from your IDE (the project is already configured for Visual Studio Code in the .vscode/launch.json file)
