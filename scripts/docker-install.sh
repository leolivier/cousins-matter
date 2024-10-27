#!/bin/bash
container=cousins-matter
image=ghcr.io/leolivier/$container
github_repo=leolivier/cousins-matter
tag='latest'
tagged_image=$image:$tag

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-f] [-d directory]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-f: force download of docker-start.sh, docker-compose.yml even if they are already present in the directory
	-d directory: the directory where cousins-matter will be installed, defaults to current directory.

It will:
	- check that docker, jq and curl are installed,
	- check if the directory exists (otherwise, create it)
	- check if the directory does not contain unwanted files to make sure we're not overwriting something. 
  - download some files from github if they don't exist or if the force flag is set.
  - create the media and data sub directories if needed.
	- pull the image '$image:latest'.
	- check if a superuser already exists in the database, otherwise run the command to create it.
  - check if a .env file exist in the chosen directory, otherwise download the .env.example from github, rename it to .env and invite the user to edit it, then exit.

EOF
	exit 0
}

function check_status() {
  status=$?;
  error=$@
  if [[ $status != 0 ]]; then
    echo "Error ($status): $error. Exiting..." >&2
    exit  $status
  fi
}

command docker >/dev/null 2>&1  # check if docker is installed and desktop running for WSL2
check_status "docker is not installed, please install it and restart the command"

command -v jq '' >/dev/null
check_status "jq is not installed, please install it and restart the command"

command -v curl >/dev/null
check_status "curl is not installed, please install it and restart the command"


directory=$PWD
force=false

while getopts ":hfqlt:d:p:" opt; do
	case $opt in
		h) usage;;
		d) directory=$OPTARG;;
		q) be_verbose=false;;
		f) force=true;;
		\?) echo "Invalid option -$OPTARG" >&2
				usage;;
	esac
done

if [[ $be_verbose == false ]]; then
    verbose() {
        :
    }
else
    verbose() {
        echo "$@"
    }
fi

# Function for checking whether an item is in a list
function is_in_list() {
	local item="$1"
	shift
	local list=("$@")
	for i in "${list[@]}"; do
		if [[ "$i" == "$item" ]]; then
			return 0
		fi
	done
	return 1
}

if [[ -d $directory ]]; then
	# Check first-level files and folders to avoid using an existing folder not dedicated to cousins-matter
	allowed_files=(.env .env.example docker-start.sh docker-compose.yml .env.backup .env.example.backup docker-start.sh.backup docker-compose.yml.backup)
	allowed_dirs=(media data scripts)
	verbose "directory $directory exists, checking it does contain only allowed files and directories..."
	for item in "$directory"/*; do
		basename_item=$(basename "$item")
		if { [[ -f "$item" ]] && ! is_in_list "$basename_item" "${allowed_files[@]}"; } || { [[ -d "$item" ]] && ! is_in_list "$basename_item" "${allowed_dirs[@]}"; }; then
			echo "$directory seems to contains files that are not allowed (e.g. $item). Only $allowed_files and $allowed_dirs are allowed."
			read -p "Do you want to continue anyway? [y/N] " -n 1 -r
			echo	
			if [[ ! $REPLY =~ ^[Yy]$ ]]; then
				echo "Please choose another directory or remove the unallowed files & folders."
				exit 2
			else
				break
			fi
		fi
	done
fi

function get_download_url() {
	last_realease=$(curl -s https://api.github.com/repos/${github_repo}/releases/latest | jq -r '.tag_name')
	echo https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}
}

mkdir -p $directory && cd $directory
mkdir -p scripts data media media/public
touch media/public/theme.css

git_url=$(get_download_url)

# download docker-start.sh, docker-compose.yml and .env.example from github if it 
# doesn't exist or if it has changed (auto-update)
for file in scripts/docker-start.sh docker-compose.yml .env.example; do
	verbose "downloading latest version of $file from github latest release."
	if [[ -f $file && ! $force ]]; then
		verbose "Backup $file to $file.backup before updating it. Please check the differences if you modified $file."
		cp $file $file.backup
	fi
	curl -s $git_url/$file -o $file
	check_status "Downloading $file failed"
done

chmod a+x scripts/docker-start.sh

function generate_secret_key() {
	echo $(tr -dc '[:alnum:]!@#$%^&*()_\-+={}[]:;<>?,./' < /dev/urandom | head -c 64)
}

if [[ ! -f .env ]]; then
	cp .env.example .env
	echo ".env didn't exist, it was created by downloading .env.example from github latest release."
	verbose "Generating secret key..."
	key=$(generate_secret_key)
	sed -i "s/SECRET_KEY=.*/SECRET_KEY='$key'  # generated automatically, do not change!/" .env
	check_status "Can't generate secret key"
	remind_dotenv=1
	echo " Please edit .env and adapt it to your neeeds before starting the site (don't change the SECRET_KEY, it was generated automatically)."
elif [[ -f .env.example.backup ]] && diff -q .env.example .env.example.backup; then
	verbose ".env.example has changed since last installation. Please compare .env.example to .env.backup and edit .env accordingly to add missing properties."
fi

verbose "checking if the database and the superuser exists..."
docker_cmd="docker run -it --entrypoint '' -v ./.env:/app/.env -v ./media:/app/media -v ./data:/app/data --name $container.tmp --rm $tagged_image"

if [[ -f data/db.sqlite3 ]]; then
	verbose "database already exists, checking if the superuser exists..."
	python_cmd="from members.models import Member; print(Member.objects.filter(is_superuser=True).exists())"
	su_exists=$($docker_cmd python manage.py shell -c "$python_cmd" 2>/dev/null)
	check_status "Can't get superuser status"
	# keep only last line to remove possible warnings
	su_exists=$(echo "$su_exists" | tail -1)
	[[ $su_exists == 'False' ]] && verbose "creating only the superuser..."
else
	su_exists="False"
	verbose "creating the database (and the superuser)..."
fi

if [[ $su_exists == 'False' ]]; then
	$docker_cmd python manage.py createsuperuser
	check_status "Can't create super user"
fi

verbose "Installation of Cousins Matter done"
if [[ $remind_dotenv == 1 ]]; then
	echo "An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site."
	sleep 5
	${EDITOR:-editor} .env
fi
