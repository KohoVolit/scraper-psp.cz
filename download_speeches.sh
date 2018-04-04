#!/bin/sh
wget -nd -r -l 1 -A "*schuz.zip" -P data/ http://www.psp.cz/eknih/2013ps/stenprot/zip/index.htm
find -name '*.zip' -exec sh -c 'unzip -o -d "${1%.*}" "$1"' _ {} \;
rm data/*.zip
find -name '*.htm' -exec sh -c 'iconv -f cp1250 -t utf8 "$1" -o "$1.new" && mv "$1.new" "$1"' _ {} \;
