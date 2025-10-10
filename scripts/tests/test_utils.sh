#!/bin/bash

# utils functions and variables to be sourced in tests

set -e

github_repo=leolivier/cousins-matter
container=cousins-matter
image=ghcr.io/$github_repo

error() {
	code=$1
	shift
  echo "Error: $@" >&2
  exit $code
}

usage() {
	cmd_desc=$@
	cat << EOF
usage: $0 [-h]  [-r] [-g] [-t tag]

$cmd_desc

args:
				-h: print this help and exit
				-r: use the image from the remote repo (if not set, uses a local image)
				-g: means the test is running in a GitHub action. Implies -r
				-t tag: the tag of the image to test. 
								If -r or -g is set, this is the tag of the remote image
								(can be a branch name or a release tag like v1.0.0). Defaults to 'latest'.
								Otherwise (-r and -g not set), this is the tag of the local image.
								Defaults to the current branch name if any else 'local'
EOF
}

get_args() {
	cmd_desc=$1
	shift
	while getopts ":hrt:" opt; do
					case $opt in
									h) usage "$cmd_desc"; exit 0;;
									r) remote=true;;
									g) github_action=true; remote=true;;
									t) tag=$OPTARG;;
									\?) echo "Invalid option -$OPTARG" >&2
											usage "$cmd_desc"; exit 1;;
					esac
	done
}

set_variables() {
	if [[ -n $github_action ]]; then
		curbranch="${GITHUB_HEAD_REF:-${GITHUB_REF#refs/heads/}}"
		echo "Branch: $curbranch"
		tag=$image:${tag:-$curbranch}
	elif [[ -z $remote ]]; then  # if we are testing a local image, compute curbranch
		curbranch=$(git rev-parse --abbrev-ref HEAD)
		curbranch=${curbranch:-local}
		tag=$container:${tag:-$curbranch}
	else  # if we are testing a remote image locally, use the tag provided
		curbranch=$tag
		tag=$image:${tag:-latest}
	fi

	if [[ $tag =~ ^$container: ]]; then  # if we are testing a local image, check git status
		if [[ -n $(git status -s) || -n $(git log @{u}..) ]]; then
			echo "###########################################################################################"
			echo "# WARNING! Some files may have been modified and not pushed to github.                    #"
			echo "# As some files are downloaded from github by manage_cousins_matter, the test might not   #"
			echo "# use modified local files. Please commit your changes before running this script.        #"
			echo "###########################################################################################"
			git status -s
			git log @{u}..
		fi
	fi
}

docker_run_cousins_matter() {

	(docker images --format "{{.Repository}}:{{.Tag}}" | grep $COUSINS_MATTER_IMAGE) || error 1 "Image $COUSINS_MATTER_IMAGE not found"

	docker compose up -d --wait --wait-timeout 45
	sleep 5  # let the system stabilize

	docker ps -a --filter name=cousins-matter --format '{{.Names}} {{.State}} "{{.Status}}"' | while read -r name state status; do
		if [[ $state != "running" ]]; then
			echo "#########################################################################################"
			echo "# ERROR! $name $status"
			echo "#########################################################################################"
			docker ps -a --filter name=cousins-matter --format '{{.Names}} {{.State}} "{{.Status}}"'
			exit 1
		fi
	done
}