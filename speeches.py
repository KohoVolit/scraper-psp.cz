# update speeches

import scrapeutils
import vpapi
import authentication
import io
import logging
from datetime import date, datetime, timedelta
import os
import json
import re
from lxml import html, etree
import dateutil.parser
import csv


current_term = "7"
vpapi.parliament('cz/psp')
vpapi.authorize(authentication.username, authentication.password)

# get all sessions
current_sessions = []
for cs in os.walk("data/"):
    m = re.findall('[0-9]{1,}', cs[0])
    try:
        current_sessions.append(m[0])
    except Exception as e:
        nothing = None
        # logging.warn(e, 'subdirectory of speeches with no number')


def get_chamber_id(term):
    """Return chamber id of the given term."""
    chamber = vpapi.getfirst('organizations', where={
        'classification': 'chamber',
        'identifiers': {'$elemMatch': {'identifier': term, 'scheme': 'psp.cz/term'}}})
    return chamber['id'] if chamber else None


chamber_id = get_chamber_id(current_term)


def get_or_create(resource, item, key=None):
    """Unless the item already exists in the resource (identified by
    `key` fields) create it. Return id of the item and a bool whether
    the item was newly created or not. If key is not given, all fields
    of the item are used as a key.
    """
    if key is None:
        key = item.keys()
    query = {field: item[field] for field in key}
    existing = vpapi.getfirst(resource, where=query)
    if existing:
        return existing['id'], False
    resp = vpapi.post(resource, item)
    return resp['id'], True


CS_MONTHS = {
    'led': 1,
    'úno': 2,
    'bře': 3,
    'dub': 4,
    'kvě': 5,
    'červen': 6,
    'červenec': 7,
    'srp': 8,
    'zář': 9,
    'říj': 10,
    'lis': 11,
    'pro': 12,
}

CS_MONTHS_REGEX = \
    'led(en|na)?|úno(ra|r)|břez(en|na)|dub(en|na)?|květ(en|na)?|červen(ce|ec)?|' + \
    'červ(en|na)?|srp(en|na)?|září?|říj(en|na)|listopa(du|d)|prosin(ec|ce)'

CS_DATE_REGEX = \
    '([0-9]{1,2}.[ ]{0,1})' + \
    '(led(en|na)|úno(ra|r)|břez(en|na)|dub(en|na)|květ(en|na)?|červen(ce|ec)|' + \
    'červ(en|na)|srp(en|na)|září|říj(en|na)|listopa(du|d)|prosin(ec|ce)) [0-9]{4}'


def extract_cs_date(text):
    match = re.search(CS_DATE_REGEX, h3, re.IGNORECASE)
    if match:
        return match.group(0)
    else:
        return None


def cs_to_utc(dt_str):
    """Converts Czech date(-time) string into ISO format in UTC time."""
    match = re.search(CS_MONTHS_REGEX, dt_str, re.IGNORECASE)
    if match:
        month = match.group(0)
        if month[:3] == 'čer':
            if len(month) > 6:
                monthn = 7
            else:
                monthn = 6
        else:
            monthn = CS_MONTHS[month[:3].lower()]
        dt_str = dt_str.replace(' ', '').replace(month, '%s.' % monthn)
    dt = dateutil.parser.parse(dt_str, dayfirst=True)
    if ':' in dt_str:
        return vpapi.local_to_utc(dt, to_string=True)
    else:
        return dt.strftime('%Y-%m-%d')


def extract_files_with_speeches(root):
    files = []
    hrefs = root.xpath('//a/@href')
    for href in hrefs:
        href_ar = href.split('#')
        if (href_ar[0] not in files) and (href_ar[0][0] == 's'):
            files.append(href_ar[0])
    return files


def extract_person_idendifier(text):
    match = re.findall('/sqw/detail.sqw\?id=([0-9]{1,})', text)
    if match:
        ex = vpapi.getfirst('people', where={'id': match[0]})
        if ex:
            return match[0]
        else:
            return None
    else:
        return None


def extract_government_identifier(text):
    match = re.findall('www.vlada.cz/cz/clenove-vlady/[a-z-]{1,}([0-9]{1,})', text)
    if match:
        # print(text)
        return match[0]
    else:
        return None


def government_to_person_identifier(text):
    pide = {
        '115390': '252',
        '115392': '6200',
        '115397': '6205',
        '115391': '443',
        '115402': '6142',
        '115401': '6184',
        '115388': '6150',
        '115393': '5269',
        '115394': '6168',
        '115389': '6138',


    }
    try:
        return pide[text]
    except Exception as e:
        nothing = None
        # print(e)
        # stop running


def extract_name(text):
    possible_roles = ["Poslanec", "Poslankyně", "Senátorka", "Senátor", "Místopředseda PSP", "Místopředsedkyně PSP", "Předseda PSP", "Předsedající", "Člen zastupitelstva hl. m. Prahy", "Zástupce veřejného ochránce práv", "Veřejná ochránkyně práv", "Předseda vlády ČR", "Primátor hl. m. Prahy", "Prezident České republiky", "Prezident Nejvyššího kontrolního úřadu", "Místopředseda vlády a ministr financí ČR", "Místopředseda vlády ČR a ministr financí", "Místopředseda vlády ČR", "Starosta Vlachovic - Vrbětic", "Generální ředitel České pošty", "Guvernér ČNB", "Náměstek hejtmana Zlínského kraje", "Náměstek hejtmana Moravskoslezského kraje", "Evropská komisařka pro spravedlnost, spotřebitele a rovnost žen a mužů", "Hejtman Libereckého kraje", "Hejtman Středočeského kraje", "Paní", "Pan", "Ministr obrany ČR", "Ministr dopravy ČR", "Ministryně práce a sociálních věcí ČR", "Ministryně pro místní rozvoj ČR", "Ministr zdravotnictví ČR", "Ministryně pro místní rozvoj ČR", "Ministr vlády ČR", "Ministr školství, mládeže a tělovýchovy ČR", "Ministr spravedlnosti ČR", "Ministryně školství, mládeže a tělovýchovy ČR"]
    for pr in possible_roles:
        text = text.replace(pr, '')
    ar = text.strip().split(' ')
    name = {
        'given_name': ar[0],
        'last_name': ar[-1],
        'name': text.strip()
    }
    return name


def extract_text(p):
    extracted = p.xpath('string()').replace('\xa0', ' ').strip()
    if extracted == '':
        return None
    else:
        return extracted


def extract_speeches(root, source):
    ps = root.xpath('//p[@align="justify"]')
    last_speaker = None
    rows = []
    for p in ps:
        ass = p.xpath('a')
        if len(ass) > 0:
            hrefs = ass[0].xpath('@href')
            if hrefs[0] == 'http://www.vlada.cz/cz/vlada/premier/':
                pident = '237'
            else:
                pident = extract_person_idendifier(hrefs[0])
                if not pident:
                    gident = extract_government_identifier(hrefs[0])
                    if gident:
                        pident = government_to_person_identifier(gident)
            if not pident:
                # enter new person
                key = ['name']
                person = {'name': extract_name(ass[0].text)['name']}
                pident, pcreated = get_or_create('people', person, key)
                # if pcreated:
                #     print(hrefs[0])
                #     print(person)
            last_speaker = pident
        text = extract_text(p)
        if text:
            row = {
                "speaker_id": last_speaker,
                "text": text,
                "source": source
            }
            rows.append(row)
    return rows


def consolidate_rows(rows, sitting_id):
    speeches = []
    i = 1
    last_speaker = None
    speech = None
    for row in rows:
        if row['speaker_id'] != last_speaker:
            if speech and speech['text'] != '':
                speeches.append(speech)
                i += 1
            speech = {
                'event_id': sitting_id,
                "position": i,
                "creator_id": row['speaker_id'],
                "sources": [
                    {
                        "url": row['source'],
                        "note": "Přepis debaty na webu Sněmovny"
                    }
                ],
                "text": ""
            }
            last_speaker = row['speaker_id']
        if row['speaker_id'] or last_speaker:
            speech['text'] += '<p>' + row['text'] + '</p>\n'
    return speeches


# if session does not exist, insert it
for cs in sorted(current_sessions):
    identifier = str(int(cs))
    session = {
        "type": "session",
        "identifier": identifier,
        "name": str(identifier) + ". schůze",
        "organization_id": chamber_id
    }
    key = ('organization_id', 'type', 'identifier')
    session_id, _ = get_or_create('events', session, key)

    current_sittings = []
    for csit in os.walk("data/" + cs + "schuz/"):
        # print("data/" + cs + "schuz/")
        for filename in csit[2]:
            m = re.findall('[0-9]{1,}-([0-9]{1,})', filename)
            try:
                current_sittings.append(m[0])
            except Exception as e:
                nothing = None

    for csit in sorted(current_sittings):
        with open("data/" + cs + "schuz/" + str(identifier) + "-" + csit + ".htm") as fin:
            # print("data/" + cs + "schuz/" + str(identifier) + "-" + csit + ".htm")
            htmltext = fin.read()
            root = html.fromstring(htmltext)
            h3 = root.xpath('string(//h3[@align="center"])').replace('\xa0', ' ')
            dat = cs_to_utc(extract_cs_date(h3))
            start_text = re.findall('(Schůze zahájena|Jednání zahájeno|Schůze pokračovala) (ve|v) (.{1,}) hod', htmltext, re.IGNORECASE)
            try:
                start_ns = re.findall('([0-9]{1,}).{1,}([0-9]{2})', start_text[0][-1])
                start_text_plus = dat + ' ' + start_ns[0][0] + ":" + start_ns[0][1]
                start_date = datetime.strptime(start_text_plus, '%Y-%m-%d %H:%M').isoformat()
            except Exception:
                start_date = datetime.strptime(dat, '%Y-%m-%d').isoformat()
            end_text = re.findall('(Schůze skončila|Jednání skončilo|Schůze přerušena|Jednání přerušeno) (ve|v) (.{1,}) hod', htmltext, re.IGNORECASE)
            try:
                end_ns = re.findall('([0-9]{1,}).{1,}([0-9]{2})', end_text[0][-1])
                end_text_plus = dat + ' ' + end_ns[0][0] + ":" + end_ns[0][1]
                end_date = datetime.strptime(end_text_plus, '%Y-%m-%d %H:%M').isoformat()
            except Exception:
                end_date = None
            sitting = {
                'name': extract_cs_date(h3),
                'type': 'sitting',
                'start_date': start_date,
                'organization_id': chamber_id,
                'parent_id': session_id,
                'identifier': csit
            }
            if end_date is not None:
                sitting['end_date'] = end_date
            key = ('organization_id', 'type', 'identifier', 'parent_id')
            sitting_id, sitting_created = get_or_create('events', sitting, key)

            # sitting_created = True
            if sitting_created:
                # insert speeches
                sfiles = extract_files_with_speeches(root)
                rows = []
                for sfile in sfiles:
                    with open("data/" + cs + "schuz/" + sfile) as sfin:
                        shtmltext = sfin.read()
                        # print("data/" + cs + "schuz/" + sfile)
                        sroot = html.fromstring(shtmltext)
                        rows = rows + extract_speeches(sroot, 'http://www.psp.cz/eknih/2013ps/stenprot/' + cs + "schuz/" + sfile)
                speeches = consolidate_rows(rows, sitting_id)
                # print(speeches)
                key = ['event_id', 'position']
                for s in speeches:
                    sid, _ = get_or_create('speeches', s, key)

                with open("dev/speeches.csv", "a") as fout:
                    csvw = csv.writer(fout)
                    for s in speeches:
                        try:
                            st = s['text'][0:50]
                        except Exception:
                            st = s['text']
                        csvw.writerow([s['creator_id'], st, s['position'], s['event_id']])

    # break
