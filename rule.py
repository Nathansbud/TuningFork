import argparse
import json
import os

from utilities import get_token

rule_file = rule_file = os.path.join(os.path.dirname(__file__), "resources", "turntable.json")
spotify = get_token()

def update_rule(uri, rule, user="6rcq1j21davq3yhbk1t0l5xnt"):
    rules = {}
    user_rules = {}
    if os.path.isfile(rule_file):
        with open(rule_file, 'r+') as rf:
            rules = json.load(rf)

    rules[user] = rules.get(user, {})
    if rule:
        rules[user][uri] = rule
    else:
        if uri in rules[user]: del rules[user][uri]
    
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

def ms(ts, ub=None):
    print(ts)
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
    parser.add_argument('-d', '--delete', '-r', '--remove', action='store_true')
    
    args = parser.parse_args()
    
    if not any([args.start, args.end, args.queue]) and not args.delete:
        exit("Must specify a track start (-s), end (-e), queue (-q), or delete (-d)")
    else:
        if args.current: track = get_track(current())
        elif args.title: track = get_track(search(args.title, args.artist))
        elif args.uri: track = get_track(args.uri)
        else:
            exit("One of: uri (-u), title (-t) + artist (-a), or current (-c) must be specified!")

        if not track: 
            exit("No track found!")
        else:
            uri = track.get('uri')
            if args.delete: 
                update_rule(uri, None)
            else:
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
                    update_rule(uri, rule)
                else:
                    print("Invalid rule!")