#!/bin/bash

# a script for building the docker image and pushing it to ghcr.io

if [[ "$1" == "-h" ]];
then echo "usage: $0 [tag1 [tag2 tag3 ...]]"
     exit 1
fi
if [[ -z $CR_PAT ]];
then echo '$CR_PAT is not defined, cannot login to ghcr.io...'
     exit 2
fi

set -e

tag=${1:-'latest'}
shift | :
other_tags=$*

image='ghcr.io/leolivier/cousins-matter'
platforms='linux/amd64,linux/arm64'

# login to ghcr.io
echo $CR_PAT | docker login ghcr.io -u leolivier  --password-stdin

# build and push
docker buildx build --platform $platforms -t $image:$tag --push .

if [[ -n $other_tags ]];
then
	for t in $other_tags;
	do 
		docker tag $image:$tag $image:$t
		docker push $image:$t
	done
fi
