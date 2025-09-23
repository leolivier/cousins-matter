#!/bin/bash

echo "This script removes all untagged versions of the package cousins-matter on ghcr.io"
echo "Images without tags can be the one of each platform (amd64, arm64, etc.) and removing them will end up in"
echo "an error \"Manifest not found\"! So USE WITH CAUTION!!!"
read -p "Type 'GO' to continue: " go
[[ $go == 'GO' ]] || exit 1

ids=/tmp/untagged_package_ids
api="https://api.github.com/users/leolivier/packages/container/cousins-matter/versions?state=active&page=1&per_page=100"
header1="Accept: application/vnd.github+json"
header2="X-GitHub-Api-Version: 2022-11-28"
header3="Authorization: Bearer $GITHUB_TOKEN"
while true;
do
  curl -L --include -X GET -H "$header1" -H "$header2" -H "$header3" "$api" > $ids
  next=$(awk '/rel="next"/ {print $2}' $ids | sed -e 's/^<//g' -e 's/>;$//g')
  rids=$(awk 'BEGIN {before=1} /\[/ {before=0} {if (before==0) print $0}' $ids | jq '.[] | select(.metadata.container.tags==[]).id')
  for id in $rids; 
  do
    delapi=$(echo $api | sed 's/\?.*//g')
    echo "removing $delapi/$id"; 
    curl -L -X DELETE -H "$header1" -H "$header2" -H "$header3" $delapi/$id;
  done
  if [[ -z $rids ]]; then
    echo "next page: $next"
    if [[ -z $next ]]; then break; fi;
    api=$next
  else
    continue
  fi
done