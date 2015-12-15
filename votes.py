# update votes

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

def option2option(opt):
    if opt == "A":
        return "yes"
    if opt == "B":
        return "no"
    if opt == "C" or opt == "F":
        return "abstain"
    if opt == "K":
        return "not voting"
    else: #M, @, W
        return "absent"


j = 0
last_ve_id = 0
voteevents = {}
people = {}
organizations = {}
terms = [1993, 1996, 1998, 2002, 2006, 2010, 2013]
terms = [2013]

for term in terms:
    logging.info('Started year ' + str(term))
    print('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip')
    zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip',zipped=True)
    #hl_hlasovani = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'s.unl')
    for i in range(1,4):
        try:
            hl_poslanec = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'h'+str(i)+'.unl')
            #savevotes(hl_poslanec)
            votes = {}
            votesli = []
            existingvotes = {}
#            terms = {}
            for rowp in hl_poslanec:
                
                
                try:
                    voteevents[rowp[1].strip()]
                except:
                    voteevents[rowp[1].strip()] = vpapi.get('vote-events', where={'identifier': rowp[1].strip()})
                r_voteevent = voteevents[rowp[1].strip()]
                
                try:
                    existingvotes[r_voteevent["_items"][0]["id"]]
                except:
                    rex = vpapi.getall('votes',where={"vote_event_id":str(j)})
                    ids = []
                    for rowx in rex:   
                        ids.append(rowx['id'])
                    if len(ids) > 0:
                        existingvotes[r_voteevent["_items"][0]["id"]] = True
                            if len(ids) < 200:
                                print(r_voteevent["_items"][0]["id"] + ": " + len(ids)
                    else:
                        existingvotes[r_voteevent["_items"][0]["id"]] = False

                if not existingvotes[r_voteevent["_items"][0]["id"]]:
                    
                    try:
                        people[rowp[0].strip()]
                    except:
                        people[rowp[0].strip()] = vpapi.get('people', where={"identifiers": {"$elemMatch": {"identifier": rowp[0].strip(), "scheme": {"$regex": "psp.cz/poslanec/*", "$options": "i"} }}})
                    r_pers = people[rowp[0].strip()]
                    
                    try: 
                        organizations[r_pers["_items"][0]["id"]]
                    except:
                        organizations[r_pers["_items"][0]["id"]] = vpapi.get('memberships',where={"person_id":r_pers["_items"][0]["id"]},embed=["organization"])   
                    r_org = organizations[r_pers["_items"][0]["id"]]
                  
                    for rowo in r_org["_items"]:
                        if rowo["organization"]["classification"] == "political group" and rowo["start_date"] <= r_voteevent["_items"][0]["start_date"]:
                            try:
                                rowo["end_date"]
                            except:
                                fine = True
                            else: 
                                if rowo["end_date"] >= r_voteevent["_items"][0]["start_date"]:
                                    fine = True
                                else:
                                    fine = False
                                # 9 lines to overcome no python's function "isset" ... )-:
                            if fine:
                                organization = rowo["organization"]
                                break
                    vote = {
                        "voter_id": r_pers["_items"][0]["id"],
                        "option": option2option(rowp[2].strip()),
                        "group_id": organization["id"],
                        "vote_event_id": r_voteevent["_items"][0]["id"]
                    }
                    last_ve_id = vote['vote_event_id']
                    try:
                        votes[r_voteevent["_items"][0]["id"]]
                    except:
                        votes[r_voteevent["_items"][0]["id"]] = []
                    votes[r_voteevent["_items"][0]["id"]].append(vote.copy())
                    j = j + 1
                    print(str(j) + ':' + str(j/200))
                    
                    
            j = 0
            votesli = []
            n = 0
#            raise(Exception)
            for k in votes:
                if (j == 1):
                    vpapi.post("votes",votesli)
                    votesli = []
                    print(str(n) + "/" + str(len(votes)))
                    print(k)
                    j = 0
                j = j + 1
                n += 1
                votesli = votesli + votes[k]
#            vpapi.post("votes",votesli)
#                vpapi.post("votes",votes[k])
#            for k in votes:
#                votesli = votesli + votes[k]
#            vpapi.post("votes",votesli)    
        except:
            nothing = 1
            logging.warning('Something went wrong with year ' + str(term) + 'and file ' + str(i) + ' (it may not exist), last vote_event_id: ' + str(last_ve_id))
    vpapi.patch('logs', db_log['id'], {'status': "finished"})
