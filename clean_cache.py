# delete all files from webcache

import os

import scrapeutils

filelist = [ f for f in os.listdir(scrapeutils.WEBCACHE_PATH) ]
for f in filelist:
    os.remove(scrapeutils.WEBCACHE_PATH + '/' + f)
