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
