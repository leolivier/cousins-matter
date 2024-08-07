#!/bin/bash

templates=$(find pages/templates/predefined/ -type f -name '*.html' ! -name default.html)
for template in $templates
do
	title=$(grep '<h1' $template |sed -e 's@^\s*<h1[^>]*>@@;s@</h1>\s*$@@;' | sed -e "s/'/\&#39;/g")
	url=$(dirname $template)/$(basename $template .html)
	url=$(echo $url|sed -e 's@pages/templates/predefined@@')'/'
	query='SELECT count(*) FROM django_flatpage WHERE url='"'"$url"'"';'
	found=$(echo "$query" | sqlite3 data/db.sqlite3)
	echo $url : found=$found
	if [[ $found -eq 1 ]];
	then echo "$title already in the database, not inserting it"
	else
		:
		content=$(cat $template|sed -e "s/'/\&#39;/g")
		echo "INSERT INTO django_flatpage (title, content, url, enable_comments, template_name, registration_required) VALUES ('$title', '$content', '$url', '0', '', '0');" | sqlite3 data/db.sqlite3
		echo "INSERT INTO django_flatpage_sites (flatpage_id, site_id) SELECT id, 1 FROM django_flatpage WHERE url='$url';" | sqlite3 data/db.sqlite3
		echo "'$title' (url: $url) inserted in the database"
	fi
done
