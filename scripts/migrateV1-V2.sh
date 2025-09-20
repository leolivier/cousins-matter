#!/bin/bash

# a script for migrating cousins-matter from v1.x to v2
# it will migrate the database from sqlite to postgres
# and update the scripts to v2

set -e
ON_RED="\e[41m"
ON_GREEN="\e[42m\e[1;37m"
ON_WHITE="\e[47m\e[1;30m"
NC="\e[0m"

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-f] [-d directory] [-b branch]

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-d directory: the directory where cousins-matter is installed, defaults to current directory.
	-b branch: the branch to use, defaults to latest release.
It will:
	- check that docker and curl or wget are installed,
	- download the latest versions of docker-compose.yml, .env.example and some scripts from github
	- add some new variables to the existing .env file, some of them in comments, some empty to be filled
	- invite the user to edit the .env file, then exit.

EOF
	exit 0
}

function error() {
	excode=$1
	shift
	echo "${ON_RED}$@${NC}" >&2
	exit $excode
}

function check_status() {
  status=$?;
  error=$@
  if [[ $status != 0 ]]; then
    error $status "$error"
  fi
}

curl_cmd=$(command -v curl)
wget_cmd=$(command -v wget)
[[ -n $curl_cmd && -n $wget_cmd ]]
check_status "curl and wget are not installed, please install one of them and restart the migration script"
[[ -n $curl_cmd ]] && download_cmd=curl || download_cmd=wget

directory=$PWD
verbose() {
	parm=""
	if [[ $1 =~ "^-.*$" ]]; then
		parm=$1
		shift
	fi
	echo $parm "$@";
}

while getopts ":hfqd:b:" opt; do
	case $opt in
		h) usage;;
		d) directory=$OPTARG
			if [[ -d $directory ]]; then
				cd $directory
			else
				error 1 "${ON_RED}Error: directory $directory does not exist${NC}"
			fi;;
		b) branch=$OPTARG;;
		q) verbose() {
        :
    };;
		\?) echo "${ON_RED}Invalid option -$OPTARG${NC}" >&2
				usage;;
	esac
done
verbose "${ON_WHITE}Migrating Cousins Matter from v1.x to v2...${NC}"

verbose "Checking if directory $directory looks like a cousins-matter project..."
make_sure="${ON_RED}Please make sure first you are in a cousins-matter directory before running this script${NC}"
[[ -f .env ]] || (error 10 "No .env file found in the directory. " $make_sure)
[[ -f docker-compose.yml ]] || (error 11 "No docker-compose.yml file found in the directory. " $make_sure)
[[ -d data ]] || (error 12 "No data directory found in the directory. " $make_sure)
[[ -f data/db.sqlite3 ]] || (error 13 "No db.sqlite3 file found in the data directory. " $make_sure)
sudo test -d . || error 14 "You must have sudo right to run this script"

migrate_database() {
	[[ -d ./data/postgres || -f ./data/postgres ]] && error 15 "${ON_RED}Postgres data directory already exists, please remove it before running this script${NC}"
	mkdir -p ./data/postgres
	sudo chown 70:70 ./data/postgres  # 70 is the id of the postgres user in the postgres image
	verbose "Starting postgres server..."
	docker compose up -d postgres
	verbose -n "Waiting for postgres to be ready"
	while true; do
		verbose -n "..."
		sleep 5
		done=$(docker logs cousins-matter-postgres 2>&1 | grep "database system is ready to accept connections"|wc -l)
		if [[ $done == 2 ]]; then
			verbose ""
			verbose "Postgres is ready, starting migration..."
			docker compose --profile migrate up migrate
			if [[ $? != 0 ]]; then
				sudo rm -rf ./data/postgres
				error 16 "Migration failed, see error message, try to fix it (usually it's a password issue), then rerun this script"
			fi
			echo "Migration done, removing pgloader container..."
			docker container rm cousins-matter-pgloader
			echo -e "${ON_GREEN}Your database has now been migrated to postgres, you can start Cousins Matter with 'docker compose up -d'${NC}"
			echo -e "${ON_RED}IMPORTANT: ${NC}"
			echo "Don't remove the db.sqlite3 file until you have checked that the postgres database has been correctly initialized."
			echo "Navigate in your site and check that all data is there."
			echo -e "${ON_WHITE}TIP:${NC} You can also have a look at the migration log in the table above and check that the number of migrated rows is correct."
			echo "Look specifically at 'members_memeber' (the number of members), 'galleries_gallery' (the number of galleries),"
			echo "'galleries_photo' (the number of photos), 'forum_post' (the number of forum posts), 'chat_chatroom' and 'chat_privatechatroom'"
			echo "(the number of public and private chat rooms), 'polls_poll' (the number of polls), 'classified_ads_classifiedad' (the number of classified ads),"
			echo "and 'troves_trove' (the number of "treasures") to make sure they are correct."
			echo "If everything is correct, you can remove the db.sqlite3 file."
			break
		else
			err=$(docker logs cousins-matter-postgres 2>&1 | grep "initdb: error:"|wc -l)
			if [[ $err -ge 1 ]]; then
				docker logs cousins-matter-postgres 2>&1 | grep "initdb: error:"
				sudo rm -rf ./data/postgres
				echo ""
				error 17 "Postgres failed to start, see error message above, try to fix it (usually it's a permission issue), then rerun this script"
			fi
		fi
	done
}

download() {
	url=$1
	file=$2
	[[ $download_cmd == "curl" ]] && silent="-s" || silent="-q"
	[[ $download_cmd == "curl" ]] && out="-o" || out="-O"
	if [[ -z $file ]]; then
		$download_cmd $silent "$url"
	else
		$download_cmd $silent "$url" $out "$file"
	fi
	check_status "Failed to download $file"
}

download_v2_scripts() {
	if [[ -z $branch ]]; then
		last_release=$($download_cmd -s https://api.github.com/repos/${github_repo}/releases/latest | grep '"tag_name":' | sed -e 's/ *"tag_name": "\(.*\)",/\1/')
		git_url=https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_release}
	else
		git_url=https://raw.githubusercontent.com/${github_repo}/refs/heads/${branch}
	fi
	for file in docker-compose.yml .env.example scripts/rotate-secrets.sh; do
		download $git_url/$file $file
	done
}

fix_permissions() {
	# replace old UID by new UID 1000 which is very often the UID of the user running the script
	sudo find . -user 5678 -exec chown 1000:1000 {} \;
}

verbose "${ON_WHITE}Fixing permissions...${NC}"
fix_permissions
verbose "${ON_WHITE}Migrating database...${NC}"
migrate_database
verbose "${ON_WHITE}Downloading v2 scripts...${NC}"
download_v2_scripts
verbose "${ON_WHITE}Rotating secrets...${NC}"
./scripts/rotate-secrets.sh
