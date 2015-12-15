# delete votes

for j in range (58382,61286):
    r = vpapi.getall('votes',where={"vote_event_id":str(j)})
    ids = []
    for row in r:   
        ids.append(row['id'])
    if len(ids) > 200 or len(ids) == 9:
        for idd in ids:    
            vpapi.delete("votes",idd)
        print("deleted " + str(j))
    else:
        print (str(j) + ": " + str(len(ids)))
    
