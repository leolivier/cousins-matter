#!/bin/bash

templates=$(find pages/templates/predefined/ -type f -name '*.html' ! -name default.html)
for template in $templates
do
	title=$(grep '<h1' $template |sed -e 's@^\s*<h1[^>]*>@@;s@</h1>\s*$@@;s@'\''@\&#39;@g;s/\xe2\x80\x8b//g')
	url=$(dirname $template)/$(basename $template .html)/
	url=${url/pages\/templates\/predefined/}
	content=$(cat $template|sed -e "s/'/\&#39;/g;s/\xe2\x80\x8b//g")
	query='SELECT content FROM django_flatpage WHERE url='"'"$url"'"';'
	found_content=$(sqlite3 data/db.sqlite3 "$query" | sed -e 's/\xe2\x80\x8b//g')
	if [[ $found_content == '' ]]; then
		query="INSERT INTO django_flatpage (title, content, url, enable_comments, template_name, registration_required) VALUES ('$title', '$content', '$url', '0', '', '0');"
		query=$query" INSERT INTO django_flatpage_sites (flatpage_id, site_id) SELECT id, 1 FROM django_flatpage WHERE url='$url';"
		query=$query" INSERT INTO pages_flatpage (flatpage_ptr_id, predefined) SELECT id, '1' FROM django_flatpage WHERE url='$url';"
		sqlite3 data/db.sqlite3 "$query"
		echo "'$title' (url: $url) inserted in the database"
	else
		flatpage_id=$(sqlite3 data/db.sqlite3 "select id from django_flatpage where url='$url';")
		if [[ $found_content != $content ]]; then
			query="SELECT updated FROM pages_flatpage WHERE flatpage_ptr_id='$flatpage_id';"
			updated=$(sqlite3 data/db.sqlite3 "$query")
			if [[ $updated == '0' ]]; then  # the page has not been updated since last import, we can safely update it
				query="UPDATE django_flatpage SET title='$title', content='$content', url='$url', enable_comments='0', template_name='', registration_required='0' WHERE url='"'"$url"'"';"
				sqlite3 data/db.sqlite3 "$query"
				echo "'$title' (url: $url) updated in the database"
			fi
		fi
		migrated=$(sqlite3 data/db.sqlite3 "select count(*) from pages_flatpage where flatpage_ptr_id='$flatpage_id';")
		if [[ $migrated == '0' ]]; then
			query="INSERT INTO pages_flatpage (flatpage_ptr_id, predefined) VALUES('$flatpage_id', '1');"
			sqlite3 data/db.sqlite3 "$query"
		fi
	fi
done
# Migrate non predefined from flatpages to pages
for flatpage_id in $(sqlite3 data/db.sqlite3 'SELECT id FROM django_flatpage;')
do
	migrated=$(sqlite3 data/db.sqlite3 "select count(*) from pages_flatpage where flatpage_ptr_id='$flatpage_id';")
	if [[ $migrated == 0 ]]; then
		query="INSERT INTO pages_flatpage (flatpage_ptr_id, predefined) VALUES('$flatpage_id', '0');"
		sqlite3 data/db.sqlite3 "$query"
	fi
done