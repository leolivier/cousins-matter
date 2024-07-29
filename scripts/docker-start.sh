#!/bin/bash

container=cousins-matter
image=ghcr.io/leolivier/$container

function usage() {
	cat << EOF

usage: $0 [-h] [-u] [-t tag] [-d directory] [-p port]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-u: if provided, $(basename $0) will first try to stop and remove an existing 'cousins-matter' container before starting a new one.
	-t tag: the tag of the image, default is 'latest'.
	-d directory: the directory where the data will be stored, will be created if it doesn't exist, defaults to current directory.
	-p port: the port where CousinsMatter app will be served, defaults to 8000.

It will first check if a .env file exist in the chosen directory.
If not, it will download the .env.example from github, rename it to .env and invite the user to edit it, then exit.
Otherwise, it will create the media and data sub directories if needed.
Then it will pull the image '$image:<tag>'.
Afterwards, it will start the image with the proper mounted volumes,the right port and the right command.
And finally, it will check if a superuser already exists in the database, other wise it will run the command to create it.

EOF
	exit 0
}

tag=latest
directory=$PWD
port=8000
update=false

while getopts ":hut:d:p:" opt; do
	case $opt in
		h) usage;;
		u) update=true;;
		t) tag=$OPTARG;;
		d) directory=$OPTARG;;
		p) port=$OPTARG;;
		\?) echo "Invalid option -$OPTARG" >&2
				usage;;
	esac
done

tagged_image=$image:$tag



# Function for checking whether an item is in a list
is_in_list() {
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
	allowed_files=(.env .env-example docker-start.sh docker-compose.yml)
	allowed_dirs=(media data)
	echo "directory $directory exists, checking it does contain only allowed files and directories..."
	for item in "$directory"/*; do
		basename_item=$(basename "$item")
		if [[ -f "$item" ]]; then
			if ! is_in_list "$basename_item" "${allowed_files[@]}"; then
				echo "$directory seems to contains files that are not allowed (e.g. $item). Only $allowed_files and $allowed_dirs are allowed."
				echo "Please choose another directory or remove the unallowed files & folders."
				exit 2
				fi
		elif [[ -d "$item" ]]; then
				if ! is_in_list "$basename_item" "${allowed_dirs[@]}"; then
					echo "$directory seems to contains folders that are not allowed (e.g. $item). Only $allowed_files and $allowed_dirs are allowed."
					echo "Please choose another directory or remove the unallowed files & folders."
					exit 2
				fi
		fi
	done
fi

mkdir -p $directory $directory/data $directory/media && cd $directory

if [[ ! -f .env ]]; then
	if [[ -s $(which curl) ]]; then
		curl -o .env https://raw.githubusercontent.com/leolivier/cousins-matter/main/.env.example
	elif [[ -s $(which wget) ]]; then
		wget -O .env https://raw.githubusercontent.com/leolivier/cousins-matter/main/.env.example
	else
		echo "Neither curl nor wget seems to be installed on your system, cannot download .env.example"
		echo "Either install curl or wget and restart the command"
		echo "or download yourself .env.example, rename it to .env and edit it"
		exit 1
	fi
	echo ".env didn't exist, it was created by downloading .env.example from github."
	echo " Please edit .env and adapt it to your neeeds then restart the command"
	exit 1
fi

if $update;
then echo "Stopping and removing the container if it exists..."
		if $(docker ps | grep "$image" > /dev/null):
		then docker stop $container
				echo "old container stopped"
		fi
		if $(docker container ls -a | grep "$container" > /dev/null);
		then docker rm $container
				echo "old container removed"
		fi
fi

echo "pulling $tagged_image..."
docker pull $tagged_image
echo "done"

echo "starting $container"
docker run --name $container -p $port:8000 -d -v ./data:/app/data -v ./.env:/app/.env -v ./media:/app/media $tagged_image
echo "started"

echo "Waiting for the container to be ready..."
for i in {1..10}; do
 sleep 1
 echo -n '.'
done
echo

echo "checking if superuser exists..."
if [[ $(docker exec cousins-matter python manage.py shell -c "from members.models import Member; print(Member.objects.filter(is_superuser=True).exists())" 2>/dev/null) == 'True' ]]; 
then echo "superuser already exists"
else echo "creating superuser..."
		docker exec -it $container python manage.py createsuperuser
fi