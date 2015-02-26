# delete duplicated votes
# duplicate is if voter_id and vote_event_id are the same
#vpapi.authorize('admin','secret')
#vpapi.parliament('cz/psp')
votes = {}
deleted = []
next = True
page = 1
while next:
    rvotes = vpapi.get("votes",page=page,max_results="50")
    for vote in rvotes["_items"]:
        try:
            votes[vote["vote_event_id"]]
        except:
            votes[vote["vote_event_id"]] = {}
            
        try:
            votes[vote["vote_event_id"]][vote["voter_id"]]
        except:
            votes[vote["vote_event_id"]][vote["voter_id"]] = vote["id"]
        else:
            #print("deleting:" + vote["id"])
            #raise(Exception,'')
            vpapi.delete("votes/"+vote["id"])
            deleted.append(vote["id"])
    page = page + 1
    print(page)
    try:
        rvotes["_links"]["next"]
    except:
        next = False
