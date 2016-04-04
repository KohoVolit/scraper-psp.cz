'''updates all json files

check vpapi.py for correct settings

'''

exec(open("organizations.py").read())
print("organizations done")
exec(open("people.py").read())
print("people done")
exec(open("memberships.py").read())
print("memberships done")
exec(open("motions_voteevents.py").read())
print("motions_voteevents done")
exec(open("votes.py").read())
print("votes done")
exec(open("clean_cache.py").read())
print("cache cleaned")
