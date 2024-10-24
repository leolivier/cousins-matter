#!/bin/bash
container=cousins-matter
image=ghcr.io/leolivier/$container

function usage() {
	cat << EOF

usage: $0 [-h] [-q] [-f] [-t tag|-l] [-p port]

Starts the cousins-matter docker container

args:
	-h: print this help and exit
	-q: quiet mode, default is verbose
	-t tag: the tag of the image
	-l: short for '-t latest'
	-f: force recreating the container even if the container already runs the requested image
	-p port: the port where CousinsMatter app will be served, defaults to 8000.

If none of '-t tag' and '-l' is provided, the script will try to see if the container is already running and reuse the same tag. 
Otherwise, it will use the 'latest' tag.
If both '-t tag' and '-l' are provided, the last provided takes precedence.

It will first check if a .env file exist in the chosen directory. If not, it will stop.
Afterwards, using docker compose, it will start the selected image with the proper mounted volumes,the right port and the right command, forcing a pull at each start.

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

tag=''
directory=$PWD
port=8000
force=false

while getopts ":hfqlt:p:" opt; do
	case $opt in
		h) usage;;
		l) tag='latest';;
		t) tag=$OPTARG;;
		p) port=$OPTARG;;
		q) be_verbose=false;;
		f) force_recreate='--force-recreate';;
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

if [[ ! -f .env ]] || diff -q .env .env.example; then
	verbose "Either .env file doesn't exist or it has not been changed since created from .env.example."
	verbose "Please edit .env according to your needs and restart the script."
	exit 1
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

if [[ -s $current_tag && $current_tag == $tag && $force == false ]]; then
	echo "Container already running with tag $current_tag, use force flag -f or another tag to update"
	exit 0
fi

last_realease=$(curl -s https://api.github.com/repos/${github_repo}/releases/latest | jq -r '.tag_name')
git_url="https://raw.githubusercontent.com/${github_repo}/refs/tags/${last_realease}"

verbose "checking if install is ok..."
[[ -f scripts/docker-start.sh && -f docker-compose.yml && -f .env && -f data/db.sqlite3 ]]
check_status "install is not ok, please run 'curl ${git_url}/scripts/docker-install.sh | bash' before starting the site"

verbose "starting $container using image $tagged_image"
COUSINS_MATTER_IMAGE=$tagged_image docker compose up $force_recreate --pull always --wait -d
check_status "Docker run failed"
verbose "Started..."
