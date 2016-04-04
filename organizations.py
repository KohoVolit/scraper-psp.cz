# update organizations

import scrapeutils
import vpapi
import authentication
import io
import logging
from datetime import date, datetime, timedelta
import os
import json

# LOGS_DIR = '/var/log/scrapers/cz/psp'
# # set-up logging to a local file
# if not os.path.exists(LOGS_DIR):
# 	os.makedirs(LOGS_DIR)
# logname = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S') + '.log'
# logname = os.path.join(LOGS_DIR, logname)
# logname = os.path.abspath(logname)
# logging.basicConfig(level=logging.DEBUG, format='%(message)s', handlers=[logging.FileHandler(logname, 'w', 'utf-8')])
# logging.getLogger('requests').setLevel(logging.ERROR)
#
# logging.info(datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S') + '\tStarted')
# db_log = vpapi.post('logs', {'status': 'running', 'file': logname, 'params': []})

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')

def save_organization(scraped):

    r = vpapi.get('organizations', where={'identifiers': {'$elemMatch': scraped["identifiers"][0]}})
    if not r['_items']:
        r = vpapi.post('organizations', scraped)
        print ("POST " + scraped['id'])
#        outid = r['id']
    else:
        # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
#        outid = r['_items'][0]['id']
        existing = r['_items'][0]
#        r = vpapi.put('organizations', existing['id'], scraped)
        #somehow vpapi.put does not work for me, so delete and post
        #vpapi.put(resource,item['id'],item)
        vpapi.delete("organizations",existing['id'])
        r = vpapi.post('organizations', scraped)
        print ("PUT " + scraped['id'])
    if r['_status'] != 'OK':
        raise Exception(scraped.name, r)
    return r['id']

zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/poslanci.zip',zipped=True)
organy = scrapeutils.zipfile2rows(zfile,'organy.unl')
# chamber:
for row in organy:
  if row[2] == '11':
    term = row[3][3:]
    org = {
      "name": row[4].strip(),
      'classification': 'chamber',
      'id': row[0].strip(),
      'identifiers': [
        {"identifier": term, 'scheme': 'psp.cz/term'},
        {"identifier": row[0].strip(), "scheme": 'psp.cz/organy'}
      ],
      'other_names': [
        {'name': 'PSP','note':'abbreviation'}
      ],
      'founding_date': scrapeutils.cs2iso(row[6].strip())
    }
    if (row[7].strip() != ''):
      org["dissolution_date"] = scrapeutils.cs2iso(row[7].strip())
    save_organization(org)


# political groups
for row in organy:
  if row[2] == '1':
    org = {
      "name": row[4].strip(),
      'classification': 'political group',
      'id': row[0].strip(),
      'identifiers': [
        {"identifier": row[0].strip(), "scheme": 'psp.cz/organy'}
      ],
      'other_names': [
        {'name': row[3].strip(), 'note':'abbreviation'}
      ],
      'founding_date': scrapeutils.cs2iso(row[6].strip())
    }
    if (row[7].strip() != ''):
      org["dissolution_date"] = scrapeutils.cs2iso(row[7].strip())
    # get parent
    r_parent = vpapi.get('organizations', where={'identifiers': {'$elemMatch': {"identifier": row[1].strip(), "scheme": "psp.cz/organy"}}})
    org["parent_id"] = r_parent["_items"][0]["id"]
    save_organization(org)
