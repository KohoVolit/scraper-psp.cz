import scrapeutils
import vpapi
import authentication

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')

votes = {}
for vote_event in vpapi.getall("vote-events"):
    votes[vote_event['id']] = []
print(len(votes))
i = 0
for vote in vpapi.getall("votes"):
    if(i/100 == round(i/100)):
        print(i)
    votes[vote_event['id']].append(vote)
    i += 1
print(len(votes))          
for i in votes:    
    if not((len(votes[i]) == 200) or (len(votes[i]) == 400)):
        print (i + ":" + len(votes[i]))

