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

command docker >/dev/null 2>&1  # check if docker is installed and desktop running for WSL2
check_status "docker is not installed, please install it and restart the command"

command -v curl >/dev/null || command -v wget >/dev/null
check_status "curl and wget are not installed, please install one of them and restart the command"


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

last_realease=$(curl -s https://api.github.com/repos/${github_repo}/releases/latest | grep '"tag_name":' | sed -e 's/ *"tag_name": "\(.*\)",/\1/')
git_url=https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}

cd $directory

verbose "downloading docker-compose.yml and .env.example from $git_url."
for file in docker-compose.yml .env.example; do
	curl -s $git_url/$file -o $file
	check_status "Downloading $file failed"
done

verbose "Creating .env from .env.example..."
mv .env.example .env

verbose "Generating secret key..."
key=$(tr -dc '[:alnum:]!@#$%^&*()_\-+={}[]:;<>?,.' < /dev/urandom | head -c 64)
sed -i "s/SECRET_KEY=.*/SECRET_KEY='$key'  # generated automatically, do not change!/" .env
check_status "Can't generate secret key"

verbose "Installation of Cousins Matter done"
echo "An editor will open in a few seconds to udpate .env file. Please adapt it to your needs before starting the site."
echo "(don't change the SECRET_KEY, it was generated automatically)."
sleep 5
${EDITOR:-editor} .env

