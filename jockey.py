import argparse
import json
import os
import sys
import math 
from enum import Enum
from utilities import get_token

rule_file = rule_file = os.path.join(os.path.dirname(__file__), "resources", "turntable.json")
spotify = get_token()
class Colors(Enum):
    DEFAULT = "\033[0m"
    RED = "\033[31;1m"
    GREEN = "\033[32;1m"
    YELLOW = "\33[33;1m"
    BLUE = '\033[34;1m'
    MAGENTA = "\033[35;1m"
    CYAN = "\033[36;1m"
    WHITE = "\033[37;1m"

def color(text, color): 
    return f"{color.value}{text}{Colors.DEFAULT.value}"

def get_rules(user="6rcq1j21davq3yhbk1t0l5xnt"):
    if os.path.isfile(rule_file):
        with open(rule_file, 'r+') as rf:
            try:
                jd = json.load(rf)
                
                tracks = jd.get('tracks', {})
                rules = jd.get(user, {})

                return rules, tracks
            except json.JSONDecodeError:
                return    

def update_rule(uri, rule, track=None, idx=None, user="6rcq1j21davq3yhbk1t0l5xnt"):
    rules = {}
    user_rules = {}
    if os.path.isfile(rule_file):
        with open(rule_file, 'r+') as rf:
            rules = json.load(rf)

    rules[user] = rules.get(user, {})
    rules['tracks'] = rules.get('tracks', {})
    
    if rule: rules[user][uri] = rule
    elif uri:
        if not rules[user]: exit("No rules found for current user!")
        elif uri in rules[user]: del rules[user][uri]
        else:
            print(f"No rule found!")
    elif idx:
        if not rules[user]: exit("No rules found for current user!")
        elif idx > len(rules[user].items()): exit(f"Removal index must be [1, {len(rules[user].items())}]!")
        
        rules[user] = {k:v for i, [k, v] in enumerate(rules[user].items(), start=1) if i != idx}
    
    if track and track.get('uri'): rules['tracks'][track.get('uri')] = track
    
    with open(rule_file, 'w+') as wf:
        json.dump(rules, wf)

        
def search(title, artist=None):
    if not title: return

    if title and artist:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}%20artist:{artist.strip()}&type=track&limit=1&offset=0").json()
    elif title:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}&type=track&limit=1&offset=0").json()
    
    return resp.get('tracks', {}).get('items', [{}])[0].get('uri') 

def current():
    return spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json().get('item', {}).get('uri')

def get_track(uri):
    if not uri: return
    uri = uri.strip()

    idx = uri if ':' not in uri else uri[uri.rindex(':')+1:]
    resp = spotify.get(f'https://api.spotify.com/v1/tracks/{idx}').json()
    if resp.get('uri'):
        return {
            'uri': resp.get('uri'),
            'duration': resp.get('duration_ms'),
            'name': resp.get('name'),
            'artist': ", ".join([artist.get('name') for artist in resp.get('artists')])
        }

def ts(ms):
    if ms is None: return None
    mins = math.floor(ms / 60000)
    ms -= mins * 60000
    secs = round(ms / 1000, 4)
    dec = secs - math.floor(secs)

    return f"{mins}:{math.floor(secs):0>2}{str(round(dec, 3))[str(round(dec, 3)).rindex('.'):] if dec > 0 else ''}"

def ms(ts, ub=None):
    process = ts.strip()
    ms = 0
    m = s = 0
    
    try:
        if not ':' in ts:    
            inp = float(ts)
            s = inp if inp < 1000 else inp / 1000    
        else:
            parts = [p.strip() for p in ts.split(':') if p]
            m = int(parts[0]) if len(parts) == 2 else 0
            s = float(parts[-1])

        ms =  (60000*m) + (1000*s)
        
        return ms if (not ub or ms <= ub) else exit(f"Input must be < {ub}!")
    except ValueError:
        exit("Input must be numeric or a mm:ss timestamp!")        
            
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser("Turntable")

    parser.add_argument('-s', '--start')
    parser.add_argument('-e', '--end')
    
    parser.add_argument('-c', '--current', action='store_true')
    parser.add_argument('-u', '--uri')
    parser.add_argument('-t', '--title')
    parser.add_argument('-a', '--artist', default=None)
    
    parser.add_argument('-q', '--queue')
    parser.add_argument('-d', '--delete', nargs='*', default='UNDEFINED')

    args = parser.parse_args()
    if sys.argv[1:]:    
        if not any([args.start, args.end, args.queue]) and args.delete == "UNDEFINED":
            exit("Must specify a track start (-s), end (-e), queue (-q), or delete (-d)")
        else:
            track = None
            if args.current: track = get_track(current())
            elif args.title: track = get_track(search(args.title, args.artist))
            elif args.uri: track = get_track(args.uri)
        
        
            if args.delete != 'UNDEFINED':
                if len(args.delete) == 0:
                    uri = (track or {}).get('uri')
                    if not uri: 
                        exit("One of: uri (-u), title (-t) + artist (-a), or current (-c) must be specified!")
                    else:
                        print(f"{color('Deleting rule', Colors.RED)} for {color(track.get('name'), Colors.CYAN)} [{color(track.get('artist'), Colors.YELLOW)}]...")
                        update_rule(uri, None, track=track)
                else:
                    try:
                        r_idxs = []
                        rules, tracks = get_rules() or [{}, {}]
                        n_rules = len(rules)
                        
                        if args.delete[0] == '*' and n_rules > 0:
                            r_idxs = range(1, n_rules + 1)
                            print(f"{color('Deleting all rules', Colors.RED)}...")                            
                        elif n_rules == 0: 
                            print("No rules found!")
                        elif args.delete[0] != '*':
                            r_idxs = sorted((int(idx) for idx in args.delete if n_rules >= int(idx) > 0), reverse=True)
                            print(f"{color('Deleting rule(s)', Colors.RED)} indexed: {color(', '.join((str(s) for s in r_idxs)).strip(), Colors.WHITE)}...")

                        for idx in r_idxs:
                            update_rule(None, None, idx=idx)
                    
                    except ValueError:
                        print("Deletion index(es) must be '*' or non-zero integers; if you forgot to quote '*', globbing likely occurred!")               
            else:
                if not track.get('uri'): exit("One of: uri (-u), title (-t) + artist (-a), or current (-c) must be specified!")
                uri = track.get('uri')
            
                start = 0
                end = track.get('duration')
                
                queue = None

                if args.end: end = ms(args.end)
                if args.start: start = ms(args.start, end)
                if args.queue:
                    if args.queue.startswith('spotify:'): queue = get_track(args.queue)
                    elif args.queue.strip().lower() == '@c': queue = get_track(current())
                    else:
                        queue = get_track(search(*(args.queue.lower().split('@by') if '@by' in args.queue.lower() else [args.queue, None])))


                rule = {}
                if start and start > 0: rule['start'] = start
                if end and end != track.get('duration'): rule['end'] = end
                if queue: rule['queue'] = queue.get('uri')

                if rule: 
                    rule['active'] = True
                    rule['mode'] = 'default'

                    print(f"{color('Upserting rule', Colors.GREEN)} for {color(track.get('name'), Colors.CYAN)} [{color(track.get('artist'), Colors.YELLOW)}]...")
                    update_rule(uri, rule, track=track)
                else:
                    print("Invalid rule!")
    else:    
        rules, tracks = get_rules() or [{}, {}]
        if rules:
            for i, [uri, rule] in enumerate(rules.items(), start=1):
                data = tracks.get(uri, {})
                q = tracks.get(rule.get('queue')) or {}
                output = ' '.join([
                    color(i, Colors.WHITE),
                    '->',
                    color(data.get('name', uri), Colors.CYAN),
                    f"[{color(data.get('artist'), Colors.YELLOW)}] - " if data.get('artist') else ' - ',
                    color(ts(rule.get('start', 0)), Colors.GREEN),
                    '<->',
                    color(ts(rule.get('end') or data.get('duration')) or 'END', Colors.RED),
                    f"- [Q: {color(q.get('name', rule.get('queue', None)), Colors.MAGENTA)}]"
                ]).replace('  ', ' ').replace(' ,', ',').strip()
                print(output)
            