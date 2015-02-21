import scrapeutils
import vpapi
import authentication
import io

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')

def save(scraped):
    import json
    r = vpapi.get('organizations', where={'identifiers': {'$elemMatch': scraped["identifiers"][0]}})
    if not r['_items']:
        r = vpapi.post('organizations', scraped)
#        outid = r['id']
    else:
        # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
        nothing = 0
#        outid = r['_items'][0]['id']
        existing = r['_items'][0]
        r = vpapi.put('organizations/%s' % existing['id'], scraped)
    if r['_status'] != 'OK':
        raise Exception(scraped.name, r)
    return r['id']
#    return outid


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
    save(org)

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
    save(org)

# people (we want mps only)
# there are several times in poslanec (for every election term)
def saveperson(scraped):
    import json
    for ident in scraped["identifiers"]:
      if ident["scheme"] == "psp.cz/osoby":
        identifier = ident
        break
               
    r = vpapi.get('people', where={'identifiers': {'$elemMatch': identifier}})
    if not r['_items']:
        r = vpapi.post('people', scraped)
    else:
        # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
        existing = r['_items'][0]
        r = vpapi.put('people/%s' % existing['id'], scraped)
    if r['_status'] != 'OK':
        raise Exception(self.name, resp)
    return r['id']


zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/poslanci.zip',zipped=True)
osoby = scrapeutils.zipfile2rows(zfile,'osoby.unl')
poslanec = scrapeutils.zipfile2rows(zfile,'poslanec.unl')


oosoby = {}
for row in osoby:
  oosoby[row[0].strip()] = row

persons = {}
terms = {}
for row in poslanec:
    oid = row[1].strip()
    try:
        terms[row[4].strip()]
    except:
        r_t = vpapi.get("organizations", where={'identifiers': {'$elemMatch': {"identifier": row[4].strip(), "scheme": "psp.cz/organy"}}})
        for ident in r_t["_items"][0]["identifiers"]:
            if ident["scheme"] == "psp.cz/term":
                terms[row[4].strip()] = ident["identifier"]
    try:
        persons[row[1].strip()]
    except:
        person = {
            "id": row[1].strip(),
            "name" : oosoby[oid][3].strip() + " " + oosoby[oid][2].strip(),
            "sort_name": oosoby[oid][2].strip() + ", " + oosoby[oid][3].strip(),
            "family_name" : oosoby[oid][2].strip(),
            "given_name" : oosoby[oid][3].strip(),
            "birth_date": scrapeutils.cs2iso(oosoby[oid][5].strip()),
            "identifiers": [
                {"identifier": row[0].strip(), "scheme": "psp.cz/poslanec/"+terms[row[4].strip()]},
                {"identifier": row[1].strip(), "scheme": "psp.cz/osoby"}
            ]
        }
        if oosoby[oid][6].strip() == "M":
            person['gender'] = 'male'
        else:
            person['gender'] = 'female'
        if oosoby[oid][1].strip() != "":
            person['honorific_prefix'] = oosoby[oid][1].strip()
        if oosoby[oid][4].strip() != "":
            person['honorific_suffix'] = oosoby[oid][4].strip()
        if oosoby[oid][8].strip() != "":
            person['death_date'] = scrapeutils.cs2iso(oosoby[oid][8].strip())
        persons[row[1].strip()] = person
    else:
        persons[row[1].strip()]["identifiers"].append(
            {"identifier": row[0].strip(), "scheme": "psp.cz/poslanec/"+terms[row[4].strip()]}
        )
    
for k in persons: 
    saveperson(persons[k])


# memberships
def savemembership(self):
    r = vpapi.get('memberships',where={'person_id': self["person_id"], 'organization_id': self["organization_id"], "role": "member", "start_date": self["start_date"]})
    if not r['_items']:
        r = vpapi.post("memberships",self)
    else:
        r = vpapi.put('memberships/%s' % r['_items'][0]['id'],self)
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
                "id": str(i),
                "start_date": datetime.strptime(row[3].strip(), '%Y-%m-%d %H').strftime('%Y-%m-%d')
            }
            if row[4].strip() != "":
                membership["end_date"] = datetime.strptime(row[4].strip(), '%Y-%m-%d %H').strftime('%Y-%m-%d')
      
            savemembership(membership)
            i = i + 1



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
    if opt == "C":
        return "abstain"
    if opt == "F" or opt == "K":
        return "not voting"
    else: #M, @, W
        return "absent"

def saveallmotionsandvoteevents(hl_hlasovani): 
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
            
            

#terms = [1993, 1996, 1998, 2002, 2006, 2010, 2013]
terms = [2013]
for term in terms:
    zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/hl-'+str(term)+'ps.zip',zipped=True)
    hl_hlasovani = scrapeutils.zipfile2rows(zfile,'hl'+str(term)+'s.unl')
    saveallmotionsandvoteevents(hl_hlasovani)


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
    for i in range(1,3):
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
#            raise(Exception)
            for k in votes:
                if (j == 10):
                    vpapi.post("votes",votesli)
                    votesli = []
                    print(str(k) + ':' + str(k/200))
                    j = 0
                j = j + 1
                votesli = votesli + votes[k]
            vpapi.post("votes",votesli)
#                vpapi.post("votes",votes[k])
#            for k in votes:
#                votesli = votesli + votes[k]
#            vpapi.post("votes",votesli)
            
        except:
            nothing = 1
