import vpapi
import authentication

vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username,authentication.password)
vpapi.timezone('Europe/Prague')

vpapi.delete("votes")
vpapi.delete("vote-events")
vpapi.delete("motions")
