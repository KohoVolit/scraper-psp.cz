# update motions and vote events
# needs to set terms manually

import scrapeutils
import vpapi
import authentication
import io
import os.path
import logging
from datetime import date, datetime, timedelta
import argparse

LOGS_DIR = '/var/log/scrapers/cz/psp'

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')

#motions, vote-events, votes:
def guess_majority(quorum,present):
    if int(quorum) == 120:
        return 'two-thirds representatives majority'
    if int(quorum) == 101 and int(present)<200:
        return 'all representatives majority'
    else:
        return 'simple majority'

def result2result(res):
    if res == "A":
        return "pass"
    else:
        return "fail"

def savemotion(self):
    r = vpapi.get('motions', where={'id': self['id']})
    if not r['_items']:
    #print(self)
        r2 = vpapi.post("motions",self)
#    else:
#        r = vpapi.put('motions/%s' % r['_items'][0]['id'],self)
#    print(r)
#    if r['_status'] != 'OK':
#        raise Exception(self.name, r)
#    else:
#        return r

def savevoteevent(self):
  r = vpapi.get('vote-events', where={'identifier':self["identifier"]})
  if not r['_items']:
    #print(self)
    r = vpapi.post("vote-events",self)
  #else:
  #  r = vpapi.patch('vote-events/%s' % r['_items'][0]['id'],self)
#    if r['_status'] != 'OK':
#        raise Exception(self.name, r)
#    else:
#        return r


def saveallmotionsandvoteevents(hl_hlasovani): 
    global test
    organizations = {}
    for row in hl_hlasovani:
        try: 
            organizations[row[1].strip()]
        except:
            organizations[row[1].strip()] = vpapi.get('organizations', where={'identifiers': {'$elemMatch': {"identifier": row[1].strip(), "scheme": "psp.cz/organy"}}}) 
        r_org = organizations[row[1].strip()]
      #r_org = vpapi.get('organizations', where={'identifiers': {'$elemMatch': {"identifier": row[1].strip(), "scheme": "psp.cz/organy"}}})
      
        motion = {
            "id": row[0].strip(),
            "organization_id": r_org["_items"][0]['id'],
            "requirement": guess_majority(row[12],row[11]),
            "result": result2result(row[14].strip()),
            "text": row[15].strip(),
#            'identifiers': [{'identifier': row[0].strip(), 'scheme': 'psp.cz/hlasovani'}],
            "sources": [{'url':"http://www.psp.cz/sqw/hlasy.sqw?g=" + row[0].strip()}]
        }
        print("motion: " + motion['id'])
#        print(motion)
        r_motion = savemotion(motion)
      
        #r_motion = vpapi.get('motions', where={'sources': {'$elemMatch': {"identifier": row[0].strip(), "scheme": "psp.cz/hlasovani"}}}) #<-wrong: should be with "sources"
#        if r_motion["_status"] == "OK":
        vote_event = {
            "id": row[0].strip(),
            "motion_id": row[0].strip(),
            'identifier': row[0].strip(),
            #"legislative_session_id": row[2].strip(),  #not implemented in api yet
            "start_date": vpapi.local_to_utc(scrapeutils.cs2iso(row[5].strip() + "T" + row[6].strip())),
            "result": result2result(row[14].strip()),
        }
        r_voteevent = savevoteevent(vote_event)
        test[row[0].strip()] = {"id":row[0].strip(),"ve":True}
        logging.info('Motion and vote-event saved: ' + str(row[0].strip()))



# set-up logging to a local file
if not os.path.exists(LOGS_DIR):
	os.makedirs(LOGS_DIR)
logname = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S') + '.log'
logname = os.path.join(LOGS_DIR, logname)
logname = os.path.abspath(logname)
logging.basicConfig(level=logging.DEBUG, format='%(message)s', handlers=[logging.FileHandler(logname, 'w', 'utf-8')])
logging.getLogger('requests').setLevel(logging.ERROR)

logging.info('Started')
db_log = vpapi.post('logs', {'status': 'running', 'file': logname, 'params': []})
            

terms = [1993, 1996, 1998, 2002, 2006, 2010, 2013]
test = {}
terms = [2013]
for term in terms:
    zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip',zipped=True)
    hl_hlasovani = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'s.unl')
    saveallmotionsandvoteevents(hl_hlasovani)
