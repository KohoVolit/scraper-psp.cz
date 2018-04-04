# update people

import scrapeutils
import vpapi
import authentication
import io
import logging
from datetime import date, datetime, timedelta
import os
import json


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
        # somehow vpapi.put does not work for me, so delete and post
#        r = vpapi.put('people', existing['id'], scraped)
        vpapi.delete("people", existing['id'])
        r = vpapi.post('people', scraped)
    if r['_status'] != 'OK':
        raise Exception(self.name, resp)
    return r['id']


zfile = scrapeutils.download('http://www.psp.cz/eknih/cdrom/opendata/poslanci.zip', zipped=True)
osoby = scrapeutils.zipfile2rows(zfile, 'osoby.unl')
poslanec = scrapeutils.zipfile2rows(zfile, 'poslanec.unl')


oosoby = {}
for row in osoby:
    oosoby[row[0].strip()] = row

persons = {}
terms = {}
for row in poslanec:
    oid = row[1].strip()
    try:
        terms[row[4].strip()]
    except Exception:
        r_t = vpapi.get("organizations", where={'identifiers': {'$elemMatch': {"identifier": row[4].strip(), "scheme": "psp.cz/organy"}}})
        for ident in r_t["_items"][0]["identifiers"]:
            if ident["scheme"] == "psp.cz/term":
                terms[row[4].strip()] = ident["identifier"]
    try:
        persons[row[1].strip()]
    except Exception:
        person = {
            "id": row[1].strip(),
            "name": oosoby[oid][3].strip() + " " + oosoby[oid][2].strip(),
            "sort_name": oosoby[oid][2].strip() + ", " + oosoby[oid][3].strip(),
            "family_name": oosoby[oid][2].strip(),
            "given_name": oosoby[oid][3].strip(),
            "birth_date": scrapeutils.cs2iso(oosoby[oid][5].strip()),
            "identifiers": [
                {"identifier": row[0].strip(), "scheme": "psp.cz/poslanec/" + terms[row[4].strip()]},
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
            {"identifier": row[0].strip(), "scheme": "psp.cz/poslanec/" + terms[row[4].strip()]}
        )

for k in persons:
    saveperson(persons[k])
