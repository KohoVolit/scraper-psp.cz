# update memberships

import scrapeutils
import vpapi
import authentication
import io
import logging
from datetime import date, datetime, timedelta
import os
import json


# memberships
def savemembership(self):
    r = vpapi.get('memberships',where={'person_id': self["person_id"], 'organization_id': self["organization_id"], "role": "member", "start_date": self["start_date"]})
    if not r['_items']:
        r = vpapi.post("memberships",self)
    else:
        #somehow vpapi.put does not work for me, so delete and post
        update = True
        try:
            if r['_items'][0]["end_date"] == self["end_date"]:
                update = False
                print("not updating: " + r['_items'][0]['id'])
        except:
            nothing = 0
        if update:
            vpapi.delete("memberships",r['_items'][0]['id'])
            self['id'] = r['_items'][0]['id']
            r = vpapi.post('memberships', self)
            print("updating: " + self['id'])
        
            
#        r = vpapi.put('memberships/%s' % r['_items'][0]['id'],self)
            if r['_status'] != 'OK':
                raise Exception(self.name, r)

zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/poslanci.zip',zipped=True)
zarazeni = scrapeutils.zipfile2rows(zfile,'zarazeni.unl')

from datetime import datetime
i = 0
for row in zarazeni:
    r_org = vpapi.get('organizations', where={'identifiers': {'$elemMatch': {"identifier": row[1].strip(), "scheme": "psp.cz/organy"}}})
    if len(r_org["_items"]) > 0:
        r_pers = vpapi.get('people', where={'identifiers': {'$elemMatch': {"identifier": row[0].strip(), "scheme": "psp.cz/osoby"}}})
        if len(r_pers["_items"]) > 0:
            membership = {
                "label": "Člen",
                "role": "member",
                "person_id": r_pers["_items"][0]['id'],
                "organization_id": r_org["_items"][0]['id'],
#                "id": str(i),
                "start_date": datetime.strptime(row[3].strip(), '%Y-%m-%d %H').strftime('%Y-%m-%d')
            }
            if row[4].strip() != "":
                membership["end_date"] = datetime.strptime(row[4].strip(), '%Y-%m-%d %H').strftime('%Y-%m-%d')
      
            savemembership(membership)
            i = i + 1
