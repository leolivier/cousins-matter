#!/bin/bash
container=cousins-matter
image=ghcr.io/leolivier/$container
github_repo=leolivier/cousins-matter

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-f] [-e] [-d directory] [-b branch]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-e: create environment only (no download, assumes the files needed to be downloaded are already there, ie in a CI/CD workflow)
	-d directory: the directory where cousins-matter will be installed, defaults to "." if -e is specified, otherwise ./cousins-matter.
     In this case, directory must not exist or be empty.
	-b branch: the branch to use, defaults to latest release.
It will:
  if '-e' is *not* specified:
	- check that docker and curl or wget are installed,
	- check that the directory is empty,
	- download docker-compose.yml, .env.example, nginx.conf and rotate-secrets.sh from github
	- Copy the .env.example to .env
	otherwise:
	- checks that we are in a dev environment (ie this script is stored in the scripts directory)
	- checks that .env file exists and is not empty
	then
	- generates a secret key or rotates it if it already exists (-e case normally)
	- generates a postgres password if it does not exist (should exist only in -e case)
	- create static, media and data directories and set the right permissions
	- starts an editor to edit .env
	and finally, if '-e' is specified, invite the user to edit .env by starting an editor.

EOF
	exit 0
}

while getopts ":hfqed:b:" opt; do
	case $opt in
		h) usage;;
		d) directory=$OPTARG;;
		b) branch=$OPTARG;;
		e) create_env_only=true;;
		q) verbose() {
        :
    };;
		\?) echo "Invalid option -$OPTARG" >&2
				usage;;
	esac
done

function check_status() {
  status=$?;
  error=$@
  if [[ $status != 0 ]]; then
    echo "Error ($status): $error. Exiting..." >&2
    exit  $status
  fi
}

sudo test -d .
check_status "You must have sudo right to run this script"

command docker >/dev/null 2>&1  # check if docker is installed and desktop running for WSL2
check_status "docker is not installed, please install it and restart the command"

if [[ -z $create_env_only ]]; then
	directory=${directory:-$PWD/cousins-matter}
else
	directory=${directory:-$PWD}
	# check that this script is in the scripts directory
	script_dir=$(basename $(cd $(dirname $0) && pwd))
	[[ $script_dir == 'scripts' ]]
	check_status "this script should be run from the scripts directory if -e selected. Are you in a devt environment?"
fi

verbose() {
    echo "$@"
}

if [[ ! -d $directory ]]; then
	verbose "directory $directory does not exist, creating it..."
	mkdir -p $directory
fi

cd $directory

if [[ -z $create_env_only ]]; then  # if not create_env_only, download files, check directory is empty
  # checking if curl or wget is installed
	curl_cmd=$(command -v curl)
	wget_cmd=$(command -v wget)
	[[ -n $curl_cmd && -n $wget_cmd ]]
	check_status "curl and wget are not installed, please install one of them and restart the command"
	[[ -n $curl_cmd ]] && download_cmd=curl || download_cmd=wget

	# check if directory is empty
	if ls -A1q $directory/ | grep -q .
	then  echo "$directory is not empty, cousins-matter must be installed in an empty directory."; exit 1
	else  verbose "$directory is empty, proceeding..."
	fi

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
		check_status "Downloading $file failed"
	}

	if [[ -z $branch ]]; then  # if no branch is specified, use the latest release
		last_realease=$($download_cmd -s https://api.github.com/repos/${github_repo}/releases/latest | grep '"tag_name":' | sed -e 's/ *"tag_name": "\(.*\)",/\1/')
		git_url=https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}
	else
		git_url=https://raw.githubusercontent.com/${github_repo}/refs/heads/${branch}
	fi


	verbose "downloading docker-compose.yml, .env.example, nginx.conf and rotate-secrets.sh from $git_url."
	mkdir -p scripts
	for file in docker-compose.yml .env.example nginx.conf scripts/rotate-secrets.sh; do
		download $git_url/$file $file
	done
	chmod a+x ./scripts/rotate-secrets.sh
	check_status "Failed to make rotate-secrets.sh executable"

	if [[ ! -f .env ]]; then
		verbose "Creating .env from .env.example..."
		mv .env.example .env
	else
	  echo "#######################################################################################"
		echo "# WARNING! .env already existed and as been moved to .env.old                         #"
		echo "# WARNING! Recreating a new .env file from .env.example                               #"
		echo "# Please check .env and copy the variables from .env.old to .env when it makes sense. #"
	  echo "#######################################################################################"
	fi

elif [[ ! -f .env ]]; then  # create_env_only is true now so .env should already be there
	echo "###########################################################################################"
	echo "# WARNING! '-e' param was provided and skipped dowloading .env.example. However, .env     #"
	echo "# does not exist in this directory. Please check .env.example, .env.old if it exists, and #"
	echo "# create a .env file to make sure all required variables are present.                     #"
	echo "###########################################################################################"
fi

verbose "Generating secret key..."
./scripts/rotate-secrets.sh
check_status "Can't generate secret key"

get_env() {
  local key="$1" val
	val=$(grep -m1 -E "^${key}=" .env | cut -d= -f2- || cut -d' ' -f1)  # second cut in case there is a comment after the value
	# if the value begins and ends with the same quotation mark (single or double), it is removed
	if [[ $val =~ ^\".*\"$ ]] || [[ $val =~ ^\'.*\'$ ]]; then
		val=${val:1:-1}
	fi
	printf '%s' "$val"
}
postgres_password=$(get_env POSTGRES_PASSWORD)
if [[ -z $postgres_password ]]; then
	verbose "Generating postgres password..."
	key=$(tr -dc '[:alnum:]./_*' < /dev/urandom | head -c 16)
	sed -i "s@POSTGRES_PASSWORD=.*@POSTGRES_PASSWORD='$key'@" .env
	check_status "Can't generate postgres password"
else
	verbose "Postgres password already exists, skipping..."
fi

# to allow the container to write in the data directory
mkdir -p ./data
sudo chmod a+w ./data
check_status "Unable to create data directory"

mkdir -p ./data/postgres
sudo chown 70:70 ./data/postgres
check_status "Unable to create postgres data directory"

mkdir -p ./media ./static
sudo chown 1000:1000 ./media ./static
check_status "Unable to create media or static data directory"

if [[ -z $create_env_only ]]; then
	echo "Installation of Cousins Matter done"
	echo "An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site."
	echo "TAKE INTO ACCOUNT THE POSSIBLE WARNINGS ON .env above"
	echo "(don't change the SECRET_KEY and the POSTGRES_PASSWORD, they were generated automatically)."
	echo "You can hit Ctrl-C to skip the editor if you want to see more details about the warnings above and edit manually .env"
	for i in $(seq 10 -1 1); do echo -n -e "The editor will open in $i seconds...\r"; sleep 1; done
	${EDITOR:-editor} .env
	echo "#############################################################################################"
	echo "# If you did set your environment variables correctly, you can now cd to your directory     #"
	echo "# $PWD and start the container with 'docker compose up -d'                                  #"
	echo "# You can check the logs with 'docker compose logs -f'                                      #"
	echo "#############################################################################################"
else
  echo "####################################"
	echo " Review of cousins-matter env done #"
	echo "####################################"
fi


