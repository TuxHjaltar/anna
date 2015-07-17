#!/bin/bash

SEARCH_URL="http://www.blocket.se/bostad/uthyres/goteborg?sort=&ss=&se=&ros=1&roe=&bs=&be=&mre=&q=&q=&q=&is=1&save_search=1&l=0&md=th&f=p&f=c&f=b&as=179_1&as=179_2&as=179_3&as=179_4&as=179_5&as=179_6&m=179"
TMP_FILE="tmp-ads"
LAST_FILE="last-ads"

wget -qO- "$SEARCH_URL"\
	| grep -P -A20 "item_\d{8}"\
	| grep title\
	| grep -P -o "http://www.blocket.se/goteborg/[^?]+"\
	> $TMP_FILE

if [ -f last-ads ]; then
	(cat last-ads && cat tmp-ads) | sort | uniq -u
fi

mv $TMP_FILE $LAST_FILE
