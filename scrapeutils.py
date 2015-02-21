#!/usr/bin/env python3

# based on https://github.com/KohoVolit/sk_nrsr_scraper/blob/master/scrapeutils.py

import os.path
import hashlib
import requests
import shutil
import html.parser
import zipfile
import io

USE_WEBCACHE = True
WEBCACHE_PATH = 'webcache'

def download(url, method='GET', data=None, url_extension='', zipped=False):
	"""Downloads and returns content from the given URL.

	If global variable USE_WEBCACHE is True, caches all received content
	and uses cached file for subsequent requests.

	In case of POST request use `url_extension` to make URLs of requests
	with different data unique.
	
	For .zip files use zipped=True and it returns zipfile.ZipFile object
	"""
	import io
	if USE_WEBCACHE:
		key = method.lower() + url + url_extension
		hash = hashlib.md5(key.encode('utf-8')).hexdigest()
		pathname = os.path.join(WEBCACHE_PATH, hash)
		if os.path.exists(pathname):
		    if zipped:
		        zip_file = zipfile.ZipFile(pathname)
		        return zip_file
		    else:
			    with open(pathname, 'r', encoding='utf-8', newline='') as f:
			    	return f.read()

	if method.upper() == 'GET':
		r = requests.get(url)
	elif method.upper() == 'POST':
		r = requests.post(url, data)
	r.raise_for_status()

	if USE_WEBCACHE:
		if not os.path.exists(WEBCACHE_PATH):
			os.makedirs(WEBCACHE_PATH)
		if zipped:
		    with open(pathname, 'wb') as f:
		        f.write(r.content)
		else:
		    with open(pathname, 'w', encoding='utf-8', newline='') as f:
			    f.write(r.text)

	if zipped:
	    zip_file = zipfile.ZipFile(io.BytesIO(r.content))
	    return zip_file
	else:
	    return r.text
	    
def zipfile2rows(zfile,filename,delimiter='|',encoding="cp1250"):
    """Extracts a csv file from zipfile and puts it into list by rows"""
    import io
    import csv
    
    items_file  = zfile.open(filename)
    items_file  = io.TextIOWrapper(items_file,encoding="cp1250")
    out = []
    for row in csv.reader(items_file,delimiter=delimiter):
        out.append(row)
    return out

def clear_cache():
	"""Clears the cache directory."""
	shutil.rmtree(WEBCACHE_PATH + '/')

def plaintext(obj, skip=None):
	"""Checks all fields of `obj` structure and converts HTML entities
	to the respective characters, strips leading and trailing
	whitespace and turns non-breakable spaces to normal ones.

	If `obj` is a dictionary, a list of keys to skip may be passed
	in the `skip` argument.
	"""
	if isinstance(obj, str):
		h = html.parser.HTMLParser()
		obj = h.unescape(obj).replace('\xa0', ' ').strip()
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			obj[i] = plaintext(v)
	elif isinstance(obj, dict):
		for k, v in obj.items():
			if isinstance(skip, (tuple, list)) and k in skip: continue
			obj[k] = plaintext(v)
	return obj

def cs2iso(datestring):
    """Converts date(-time) string in CS format (dd.mm.YYYY) to ISO
    format (YYYY-mm-dd).
    """
    from datetime import datetime   # http://stackoverflow.com/a/9182195
    datestring = datestring.replace('. ', '.')
    try:
        return datetime.strptime(datestring, '%d.%m.%Y').date().isoformat()
    except ValueError:
        return datetime.strptime(datestring, '%d.%m.%YT%H:%M').isoformat('T')
