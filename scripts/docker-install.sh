#!/bin/bash
container=cousins-matter
image=ghcr.io/leolivier/$container
github_repo=leolivier/cousins-matter

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-f] [-d directory]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-d directory: the directory where cousins-matter will be installed, defaults to ./cousins-matter. Directory must not exist or be empty.

It will:
	- check that docker and curl or wget are installed,
	- download docker-compose.yml and .env.example from github
	- Copy the .env.example to .env and invite the user to edit it, then exit.

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

sudo test -d .
check_status "You must have sudo right to run this script"

command docker >/dev/null 2>&1  # check if docker is installed and desktop running for WSL2
check_status "docker is not installed, please install it and restart the command"

curl_cmd=$(command -v curl)
wget_cmd=$(command -v wget)
[[ -n $curl_cmd && -n $wget_cmd ]]
check_status "curl and wget are not installed, please install one of them and restart the command"
[[ -n $curl_cmd ]] && download_cmd=curl || download_cmd=wget

directory=$PWD/cousins-matter
verbose() {
    echo "$@"
}

while getopts ":hfqd:" opt; do
	case $opt in
		h) usage;;
		d) directory=$OPTARG;;
		q) verbose() {
        :
    };;
		\?) echo "Invalid option -$OPTARG" >&2
				usage;;
	esac
done

if [[ -d $directory ]]; then
	verbose "directory $directory exists, checking it does not contain any file..."
	if ls -A1q $directory/ | grep -q .
	then  echo "$directory is not empty, cousins-matter must be installed in an empty directory."; exit 1
	else  verbose "$directory is empty, proceeding..."
	fi
else
	verbose "directory $directory does not exist, creating it..."
	mkdir -p $directory
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

last_realease=$($download_cmd -s https://api.github.com/repos/${github_repo}/releases/latest | grep '"tag_name":' | sed -e 's/ *"tag_name": "\(.*\)",/\1/')
git_url=https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}

cd $directory

verbose "downloading docker-compose.yml, .env.example, nginx.conf and rotate-secrets.sh from $git_url."
mkdir scripts
for file in docker-compose.yml .env.example nginx.conf scripts/rotate-secrets.sh; do
	download $git_url/$file $file
done
chmod a+x ./scripts/rotate-secrets.sh
check_status "Failed to make rotate-secrets.sh executable"

if [[ ! -f .env ]]; then
	verbose "Creating .env from .env.example..."
	mv .env.example .env
else
	echo "WARNING! Skipping .env creation, .env already exists but might not contain all required variables."
	echo "Please check .env.example and .env to make sure all required variables are present."
fi

verbose "Generating secret key..."
./scripts/rotate-secrets.sh
check_status "Can't generate secret key"

verbose "Generating postgres password..."
key=$(tr -dc '[:alnum:]./_*' < /dev/urandom | head -c 16)
sed -i "s@POSTGRES_PASSWORD=.*@POSTGRES_PASSWORD='$key'@" .env
check_status "Can't generate postgres password"

mkdir -p ./data/postgres
sudo chmod a+w ./data
sudo chown 70:70 ./data/postgres
check_status "Unable to create postgres data directory"

verbose "Installation of Cousins Matter done"
echo "An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site."
echo "(don't change the SECRET_KEY, it was generated automatically)."
sleep 5
${EDITOR:-editor} .env

