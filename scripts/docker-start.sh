#!/bin/bash
container=cousins-matter
image=ghcr.io/leolivier/$container
github_repo=leolivier/cousins-matter

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

Prerequisites:
	- docker
	- jq
	- curl
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

which docker >/dev/null
check_status "docker is not installed, please install it and restart the command"

which jq >/dev/null
check_status "jq is not installed, please install it and restart the command"

which curl >/dev/null
check_status "curl is not installed, please install it and restart the command"

tag=''
directory=$PWD
port=8000
update=false
force=false

while getopts ":hufqlt:d:p:" opt; do
	case $opt in
		h) usage;;
		u) update=true;;
		l) tag='latest';;
		t) tag=$OPTARG;;
		d) directory=$OPTARG;;
		p) port=$OPTARG;;
		v) be_verbose=false;;
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

current_tag=$(docker container ls 2>/dev/null | awk -v name="$container" '$NF == name {split($2, a, ":"); print (a[2] ? a[2] : "latest")}');

if [[ -z $tag ]]; then
	if [[ -z $current_tag ]]; then
		verbose "no existing container found, looking for images..."
        images=$(docker images 2>/dev/null | awk -v name="$image" '$1 == name {print($2);}');
		if [[ -n $images ]]; then
		  verbose "found $image with tag(s) $images"
		  for img in $images; do
		    tag=$img
		    if [[ $img == 'latest' ]]; then
		      break;
		    fi
		  done
	      verbose "...will use $tag tag"
		else
			verbose "No image found, will use 'latest' tag"
			tag='latest'
		fi
	else
		verbose "...reusing existing container tag: $current_tag"
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

def get_download_url() {
	last_realease=$(curl -s https://api.github.com/repos/${github_repo}/releases/latest | jq -r '.tag_name')
	echo https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}
}

mkdir -p $directory $directory/data $directory/media && cd $directory
git_url=$(get_download_url)
# download docker-compose.yml from github if it doesn't exist
if [[ ! -f docker-compose.yml ]]; then
	verbose "downloading docker-compose.yml from github latest release."
	curl $git_url/docker-compose.yml -o docker-compose.yml
fi
if [[ ! -f .env ]]; then
	curl -o .env $git_url/.env.example
	echo ".env didn't exist, it was created by downloading .env.example from github latest release."
	echo " Please edit .env and adapt it to your neeeds then restart the command"
	exit 1
fi

verbose "starting $container using image $tagged_image"
COUSINS_MATTER_IMAGE=$tagged_image docker compose up --pull always --wait -d
check_status "Docker run failed"
verbose "started"

verbose "checking if superuser exists..."
su_exists=$(docker exec $container python manage.py shell -c "from members.models import Member; print(Member.objects.filter(is_superuser=True).exists())" 2>/dev/null)
check_status "Can't get superuser status"

# keep only last line to remove possible warnings
su_exists=$(echo "$su_exists" | tail -1)

if [[ $su_exists == 'True' ]]; then
	verbose "superuser already exists"
else
	echo "creating superuser..."
	docker exec -it $container python manage.py createsuperuser
	check_status "Can't create super user"
fi

verbose "done"
