#!/bin/bash

container=cousins-matter
image=ghcr.io/leolivier/$container

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-u] [-f] [-t tag|-l] [-d directory] [-p port]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-u: if provided, $(basename $0) will first try to stop and remove an existing 'cousins-matter' container before starting a new one.
	-t tag: the tag of the image
	-l: short for '-t latest'
	-f: force restart even if the container already runs the requested image (if -l or tag=latest, restart even if the latest image is already running)
	-d directory: the directory where the data will be stored, will be created if it doesn't exist, defaults to current directory.
	-p port: the port where CousinsMatter app will be served, defaults to 8000.


If none of '-t tag' and '-l' is provided, the script will try to see if the container is already running and reuse the same tag. 
Otherwise, it will use the 'latest' tag.
If both '-t tag' and '-l' are provided, the last provided takes precedence.

It will first check if a .env file exist in the chosen directory.
If not, it will download the .env.example from github, rename it to .env and invite the user to edit it, then exit.
Otherwise, it will create the media and data sub directories if needed.
Then it will pull the image '$image:<tag>'.
Afterwards, it will start the image with the proper mounted volumes,the right port and the right command.
And finally, it will check if a superuser already exists in the database, other wise it will run the command to create it.

IMPORTANT: This script uses jq and either curl or wget. If neither is installed, the script will exit with an error.
EOF
	exit 0
}

if [[ -z $(which jq) ]]; then
	echo "jq is not installed, please install it and restart the command"
	exit 1
fi

tag=''
directory=$PWD
port=8000
update=false
current_tag=$(docker container ls 2>/dev/null | awk -v name="$container" '$NF == name {split($2, a, ":"); print (a[2] ? a[2] : "latest")}');
force=false
be_verbose=true

while getopts ":hufqlt:d:p:" opt; do
	case $opt in
		h) usage;;
		u) update=true;;
		l) tag='latest';;
		t) tag=$OPTARG;;
		d) directory=$OPTARG;;
		p) port=$OPTARG;;
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

if [[ -z $tag ]]; then
	if [[ -z $current_tag ]]; then
		verbose "no existing container found, using 'latest' tag"
		tag='latest'
	else
		verbose "reusing existing container tag: $current_tag"
		tag=$current_tag
	fi
fi

tagged_image=$image:$tag

if [[ -s $current_tag && $current_tag == $tag && $update != true && $force == false ]]; then
	echo "Container already running with tag $current_tag, use update flag -u or another tag to update"
	exit 0
fi

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
	verbose "directory $directory exists, checking it does contain only allowed files and directories..."
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

# Get the local architecture
arch=$(docker version -f '{{.Server.Arch}}')

# Image digest function
function get_image_digest() {
	docker image inspect --format='{{index .RepoDigests 0}}' "$1" 2>/dev/null | cut -d'@' -f2
}

function pull_image() {
	tagged_image=$1
	verbose "pulling $tagged_image..."
	docker pull $tagged_image
	verbose "done"
}

# Get the remote image manifest
manifest=$(docker manifest inspect "${tagged_image}")

if [ -z "$manifest" ]; then
	echo "Unable to retrieve manifest for ${tagged_image}"
	exit 5
fi

# Find the digest matching the local architecture
remote_digest=$(echo "$manifest" | jq -r ".manifests[] | select(.platform.architecture == \"$arch\") | .digest")

if [ -z "$remote_digest" ]; then
	echo "Remote digest for architecture $arch of ${tagged_image} not found"
	exit 5
fi

# Get the local image digest
local_digest=$(get_image_digest "${tagged_image}")

if [ -z "$local_digest" ]; then
	verbose "Local image not found: ${tagged_image}"
	pull_image ${tagged_image}
else
	# Compare digests
	verbose "Local	Digest : $local_digest"
	verbose "Remote Digest : $remote_digest"

	if [ "$local_digest" != "$remote_digest" ]; then
		verbose "An update is available for ${tagged_image} (architecture: $arch)"
		pull_image ${tagged_image}
	fi
fi

# check if the container is already running the latest image
update=true
if [ -n "$current_tag" ]; then
	container_image_id=$(docker inspect --format='{{.Image}}' "$container" 2>/dev/null)
	if [ -z "$container_image_id" ]; then
		verbose "Container not found : $container"
	else
		container_digest=$(get_image_digest "$container_image_id")
		verbose "Digest of the container: $container_digest"

		if [ "$container_digest" != "$local_digest" ]; then
			verbose "The container uses an image different from the latest local image."
		else
			verbose "The container already uses the current local image."
			update=false
		fi
	fi
fi

if [[ "$update" == true || $force == true ]]; then
	verbose "Stopping and removing the container if it exists..."
	if $(docker ps | grep "$container" > /dev/null); then
		docker stop $container
		verbose "old container stopped"
	fi
	if $(docker container ls -a | grep "$container" > /dev/null); then
		docker rm $container
		verbose "old container removed"
	fi
	verbose "starting $container"
	docker run --name $container -p $port:8000 -d -v ./data:/app/data -v ./.env:/app/.env -v ./media:/app/media $tagged_image
	verbose "started"

	verbose "Waiting for the container to be ready..."
	for i in {1..10}; do
		sleep 1
		echo -n '.'
	done
	verbose

	verbose "checking if superuser exists..."
	if [[ $(docker exec cousins-matter python manage.py shell -c "from members.models import Member; print(Member.objects.filter(is_superuser=True).exists())" 2>/dev/null) == 'True' ]]; then
		verbose "superuser already exists"
	else
		echo "creating superuser..."
		docker exec -it $container python manage.py createsuperuser
	fi

fi
verbose "done"
