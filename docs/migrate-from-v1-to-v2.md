# Migrate from Version 1 to Version 2

## Introduction

The version 2 of Cousins Matter is a big rewrite of the version 1 and is not directly compatible with the version 1. 
Amongst other big changes:

* the database has been migrated from sqlite3 to postgresql to allow for better performance and scalability.
* cousins matter is now composed of at least 4 docker containers:

	* the web server
	* the database
	* redis
	* the asynchronous tasks server

	and will thus require docker compose to run.

## Prerequisites

You have to have Cousins Matter v1 installed and working on your system.

You will also need a Python 3.12+ environment to run the migration script.

## Procedure

1. Stop Cousins Matter v1

	```
	cd <cousins-matter-v1-directory>
	docker compose down
	```

1. Download the Cousins Matter admin script

	Please replace in the link below the <release\> placeholder with the current release of Cousins Matter:
![GitHub Release](https://img.shields.io/github/v release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
	mkdir scripts
	curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
	```

1. Run the migration script

	```
	python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <release>]
	```

	If release is not provided, it will migrate to the latest release of v2.X (recommanded).

	**Pay attention to the log of the migration script!** It will show you the progress of the migration and any potential issues or actions to take.

1. Update your settings

	The Cousins Matter v2 settings are different from v1. Please update your .env file to match the settings of Cousins Matter v2.

	The Cousins Matter v2 settings are detailed in the [Settings](settings.md) page.
	In particular, the migration updates the .env.example file to match the settings of Cousins Matter v2. So, please compare this new .env.example file with your .env file and update your .env file accordingly. 
	
	Pay also attention that some defaults have changed. For instance:

	* ALLOW_MEMBERS_TO_CREATE_MEMBERS and ALLOW_MEMBERS_TO_INVITE_MEMBERS are now True by default
	* ALLOWED_HOSTS now contains the value of SITE_DOMAIN ('127.0.0.1,localhost,$SITE_DOMAIN') by default
	* DARK_MODE is now False by default
	* SESSION_COOKIE_DOMAIN is now set to .$SITE_DOMAIN by default
	* SITE_PORT is now set to 0 if SITE_DOMAIN is set, 8000 if not

	Also, new variables have been added to the .env file but they have decent default values.

	* POSTGRES_USER=cousinsmatter
	* POSTGRES_DB=cousinsmatter
	* POSTGRES_HOST=postgres
	* POSTGRES_PASSWORD is computed automatically at migration time
	* PREVIOUS_SECRET_KEYS is computed automatically at migration time (and the SECRET_KEY is rotated)

1. Start Cousins Matter v2

	```
	docker compose pull  # get all the images
	docker compose up -d
	```

