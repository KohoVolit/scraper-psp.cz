import scrapeutils
import vpapi
import authentication
import io

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')


#motions, vote-events, votes:
def guess_majority(quorum,present):
    if int(quorum) == 121 or int(quorum) == 120:
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

#now faster (just including)
def savemotion(self):
    #r = vpapi.get('motions', where={'identifiers': {'$elemMatch': self["identifiers"][0]}})
#   if not r['_items']:
    print(self)
    r = vpapi.post("motions",self)
#   else:
#       r = vpapi.put('motions/%s' % r['_items'][0]['id'],self)
    if r['_status'] != 'OK':
        raise Exception(self.name, r)
    else:
        return r

#now faster (just including)
def savevoteevent(self):
  #r = vpapi.get('vote-events', where={'identifier':self["identifier"]})
  #if not r['_items']:
    print(self)
    r = vpapi.post("vote-events",self)
  #else:
  #  r = vpapi.patch('vote-events/%s' % r['_items'][0]['id'],self)
    if r['_status'] != 'OK':
        raise Exception(self.name, r)
    else:
        return r

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

def saveallmotionsandvoteevents(hl_hlasovani,rosnicka_vote_events): 
    organizations = {}
    for row in hl_hlasovani:
        if row[0].strip() in rosnicka_vote_events:
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
                #'identifiers': [{'identifier': row[0].strip(), 'scheme': 'psp.cz/hlasovani'}]
                "sources": [{'url':"http://www.psp.cz/sqw/hlasy.sqw?g=" + row[0].strip()}]
            }
            print(motion)
            r_motion = savemotion(motion)
          
            #r_motion = vpapi.get('motions', where={'sources': {'$elemMatch': {"identifier": row[0].strip(), "scheme": "psp.cz/hlasovani"}}}) #<-wrong: should be with "sources"
            if r_motion["_status"] == "OK":
                vote_event = {
                    "id": row[0].strip(),
                    "motion_id": r_motion['id'],
                    'identifier': row[0].strip(),
                    #"legislative_session_id": row[2].strip(),  #not implemented in api yet
                    "start_date": vpapi.local_to_utc(scrapeutils.cs2iso(row[5].strip() + "T" + row[6].strip())),
                    "result": result2result(row[14].strip()),
                }
                r_voteevent = savevoteevent(vote_event)
            
            
rosnicka_vote_events = ["6858", "2901", "9096", "10163", "10165", "10294", "12667", "13454", "12670", "12671", "12672", "12673", "13187", "13508", "14938", "20233", "24341", "27824", "28018", "38655", "39516", "39522", "45019", "45531", "45908", "52918", "55672", "57625", "58818", "58869"]

terms = [1993, 1996, 1998, 2002, 2006, 2010, 2013]
#terms = [2013,2010]
for term in terms:
    zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip',zipped=True)
    hl_hlasovani = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'s.unl')
    saveallmotionsandvoteevents(hl_hlasovani,rosnicka_vote_events)


def savevotes(hl_poslanec):
    votes = {}
    voteevents = {}
    people = {}
    organizations = {}
    terms = {}
    for rowp in hl_poslanec:
        #if rowp[0] == 0: chybne hlasovani v db, viz http://www.psp.cz/sqw/hlasy.sqw?g=58297
    #  try:
    #    terms[hl_hlasovani[i][1].strip()]
    #  except:
    #    r_t = vpapi.get("organizations", where={'identifiers': {'$elemMatch': {"identifier": hl_hlasovani[0][1].strip(), "scheme": "psp.cz/organy"}}})
    #    for ident in r_t["_items"][0]["identifiers"]:
    #      if ident["scheme"] == "psp.cz/term":
    #        terms[hl_hlasovani[0][1].strip()] = ident["identifier"]
        try:
            voteevents[rowp[1].strip()]
        except:
            voteevents[rowp[1].strip()] = vpapi.get('vote-events', where={'identifier': rowp[1].strip()})
        r_voteevent = voteevents[rowp[1].strip()]
      
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
        try:
            votes[r_voteevent["_items"][0]["id"]]
        except:
            votes[r_voteevent["_items"][0]["id"]] = []
        votes[r_voteevent["_items"][0]["id"]].append(vote.copy())
#    for k in votes:
#        vpapi.post("votes",votes[k])
    vpapi.post("votes",votes)


j = 0
for term in terms:
    zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip',zipped=True)
    #hl_hlasovani = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'s.unl')
    for i in range(1,4):
        try:
            hl_poslanec = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'h'+str(i)+'.unl')
            #savevotes(hl_poslanec)
            #savevotes(hl_poslanec)
            votes = {}
            votesli = []
            voteevents = {}
            people = {}
            organizations = {}
            terms = {}
            for rowp in hl_poslanec:
                if rowp[1].strip() in rosnicka_vote_events:
                    try:
                        voteevents[rowp[1].strip()]
                    except:
                        voteevents[rowp[1].strip()] = vpapi.get('vote-events', where={'identifier': rowp[1].strip()})
                    r_voteevent = voteevents[rowp[1].strip()]
                  
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
                if (j == 10):
                    vpapi.post("votes",votesli)
                    votesli = []
                    print(str(n) + "/" + str(len(votes)))
                    j = 0
                j = j + 1
                n += 1
                votesli = votesli + votes[k]
            vpapi.post("votes",votesli)
#                vpapi.post("votes",votes[k])
#            for k in votes:
#                votesli = votesli + votes[k]
#            vpapi.post("votes",votesli)
            
        except:
            nothing = 1
