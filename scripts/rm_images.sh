#!/bin/bash

echo "This script removes all untagged versions of the package cousins-matter on ghcr.io"
echo "Images without tags can be the one of each platform (amd64, arm64, etc.) and removing them will end up in"
echo "an error \"Manifest not found\"! So USE WITH CAUTION!!!"
read -p "Type 'GO' to continue: " go
[[ $go == 'GO' ]] || exit 1

while true;
do
  ids=/tmp/untagged_package_ids
  api='/user/packages/container/cousins-matter/versions'
  header1="Accept: application/vnd.github+json"
  header2="X-GitHub-Api-Version: 2022-11-28"
  gh api -H "$header1" -H "$header2" $cmd $api | jq '.[] | select(.metadata.container.tags==[]).id' > $ids
  if [[ $(cat $ids | wc -l) == 0 ]]; then break; fi;
  cat $ids | while read id; 
  do 
    echo "removing $id"; 
    gh api --method DELETE -H "$header1" -H "$header2" $api/$id;
  done
done
