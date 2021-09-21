from utilities import (
    call_applescript, 
    search, get_token, 
    SongParser, SongException,
    color, Colors
)

import sys
import os
import json
import argparse
import shlex
from itertools import permutations

from scraper import get_lyrics


group_file = os.path.join(os.path.dirname(__file__), "resources", "queue.json")
cache_file = os.path.join(os.path.dirname(__file__), "resources", "cache.json")
PART_SEPARATOR = '<--|-->'


def load_groups():
    if not os.path.isfile(group_file):
        with open(group_file, 'w+') as gf: json.dump({}, gf)
    
    with open(group_file, 'r') as gf: 
        return json.load(gf)

spotify = get_token()
groups = load_groups()

def get_track(uri, formatted=True):
    if not uri: return
    uri = uri.strip()

    idx = uri if ':' not in uri else uri[uri.rindex(':')+1:]
    resp = spotify.get(f'https://api.spotify.com/v1/tracks/{idx}').json()
    if resp and formatted:
        return {
            'uri': resp.get('uri'),
            'name': resp.get('name'),
            'artist': ", ".join([artist.get('name') for artist in resp.get('artists')])
        }
    
    return resp


def current(): return spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json().get('item', {})
def current_uri(): current().get('uri')
def current_lyrics():
    try:
        current_track = current()
    except json.decoder.JSONDecodeError:
        return

    album_artists = [artist.get('name') for artist in current_track.get('album', {}).get('artists', [])]
    lyrics = get_lyrics(album_artists[0], current_track.get('name'))
    if lyrics: 
        return {
            "artist": album_artists[0],
            "album": current_track.get("album").get("name"),
            "title": current_track.get("name"), 
            "lyrics": lyrics
        }
    else:
        for p in permutations(album_artists):
            lyrics = get_lyrics(" and ".join(p), current_track.get('name'))
            if lyrics:
                return {
                    "artist": " and ".join(p),
                    "album": current_track.get("album").get("name"),
                    "title": current_track.get("name"), 
                    "lyrics": lyrics
                }

        return {
            "artist": album_artists[0],
            "album": current_track.get("album").get("name"),
            "title": current_track.get("name"), 
            "lyrics": None
        }
    
def add_group():
    tracks = []
    name = input("Queue Group Name: ")
    
    parser = SongParser("Song Parser")
    parser.add_argument('title', nargs="?")
    parser.add_argument('artist', nargs="?")
    parser.add_argument('-c', '--current', action='store_true')
    parser.add_argument('-u', '--uri')

    print("Input track name + artist or URI; type SAVE when finished!")
    adding = True
    
    while adding:
        candidate_track = input(f"Item {len(tracks) + 1}: ")
        if candidate_track.strip().upper() == 'SAVE':
            if len(tracks) > 0:
                with open(group_file) as gf:
                    try: 
                        groups = json.load(gf) 
                    except json.JSONDecodeError: 
                        groups = {}
                
                groups[name] = tracks
                with open(group_file, 'w+') as gf:
                    json.dump(groups, gf)
            else:
                print("No tracks specified!")
            adding = False
        else:
            try:
                track = {}           
                args = parser.parse_args(shlex.split(candidate_track))
                if args.title: track = get_track(search(args.title, args.artist, spotify))
                elif args.uri: track = get_track(args.uri)
                elif args.current: track = get_track(current_uri())
                else:
                    raise SongException("Invalid track specifier! Provide artist (and track), else specify current (-c) or uri (-u)!")

                if track:
                    confirm = input(f"Found track: {track.get('name')} by {track.get('artist')}. Add to group {name} (y/n)? ").lower().strip()
                    if confirm == 'y': tracks.append(track)
            except SongException as e:
                print(e)
            
            
def enqueue(title=None, artist=None, times=1, last=None, group=None, uri=None):
    track_uris = []
    group_data = []    
    if group:
        with open(group_file) as gf:
            try:
                groups = json.load(gf)
            except json.JSONDecodeError:
                groups = {}
        
        group_data = groups.get(group, [])
        tracks = group_data
        
    elif title: 
        if uri: data = get_track(uri.split(":")[-1], False)
        else:
            if artist:
                st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}%20artist:{artist}&type=track&limit=1&offset=0").json()
            else: 
                st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}&type=track&limit=1&offset=0").json()
            
            data = st['tracks']['items'][0] if st['tracks']['items'] else {}
        
        tracks = [{
            'name': data.get('name'), 
            'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
            'uri': data.get('uri')
        }] if data else []

    elif last:
        previous = spotify.get(f"https://api.spotify.com/v1/me/player/recently-played?limit={last}").json()
        responses = [s.get('track', {}) for s in previous.get('items', [])][::-1]

        tracks = [{
            'name': data.get('name'),
            'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
            'uri': data.get('uri')
        } for data in responses]
        
    else:
        current = spotify.get("https://api.spotify.com/v1/me/player/currently-playing")
        if current.status_code == 204: 
            print("No track currently playing!")
            tracks = []
        else:
            data = current.json().get('item', {})
            tracks = [{
                'name': data.get('name'), 
                'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
                'uri': data.get('uri')
            }]

    if tracks:
        for i in range(times):  
           for t in tracks:
               spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={t.get('uri')}")

        if last:
            print(f"""Added{' ' + str(last) if last > 1 else ''} last played item{'s' if last > 1 else ''} ({', '.join([f"{t.get('name')} by {t.get('artist')}" for t in tracks])}) to queue {times}x!""")
        else:
            print("Added " + ", ".join([f"{t.get('name')} by {t.get('artist')}" for t in tracks]) + f" to queue {times}x!")

        return tracks
    else:
        print("Could not find track(s)!")



def remember_track(artist, title, track):
    memory = {}
    if os.path.isfile(cache_file):
        with open(cache_file, "r") as cf:
            try: 
                memory = json.load(cf)
            except:
                memory = {}

    memory[f"{(artist or '').lower()}{PART_SEPARATOR}{(title or '').lower()}"] = {
        'name': track.get('name'), 
        'artist': track.get('artist'),
        'uri': track.get('uri')
    }
    with open(cache_file, "w+") as wf:
        json.dump(memory, wf)


def queue_track():
    parser = argparse.ArgumentParser(description="Spotify track queuer")

    parser.add_argument('title', nargs='?', default=None)
    parser.add_argument('artist', nargs='?', default=None)

    #This arg achieves nothing, I just want queue and queue -c to do the same thing
    parser.add_argument('-c', '--current', action="store_true")
    parser.add_argument('-o', '--open', action="store_true")

    parser.add_argument('-t', '--times', nargs='?', default=1, const=1, type=int)
    parser.add_argument('-p', '--previous', nargs='?', const=1, type=int)

    parser.add_argument('-l', '--list_groups', action='store_true')
    parser.add_argument('-a', '--add_group', action='store_true')
    parser.add_argument('-d', '--delete_group')
    parser.add_argument('-g', '--group', type=str)
    
    parser.add_argument('-r', '--remember', nargs='*', default=None)
    parser.add_argument('-f', '--forget', action='store_true')

    args = parser.parse_args()
    if args.open: os.system(f'subl "{__file__}"')
    elif args.add_group: add_group()
    elif args.delete_group: 
        with open(group_file, 'r+') as gf:
            try:
                groups = json.load(gf)
                if args.delete_group in groups: del groups[args.delete_group]
                else: print(f"Group {args.delete_group} not found!")
            except json.JSONDecodeError:
                print("No groups found!")
                groups = {}
        
        with open(group_file, 'w+') as gf:
            json.dump(groups, gf)

    elif args.list_groups: 
        with open(group_file) as gf:
            try:
                groups = json.load(gf)
                for name, data in groups.items():
                    tracks = ", ".join([
                        f"{color(d.get('name'), Colors.CYAN)} [{color(d.get('artist'), Colors.YELLOW)}]" 
                        for d in data
                    ])
                    print(f"{color(name, Colors.GREEN)}: {tracks}")
            except json.JSONDecodeError:
                pass

    else:
        with open(cache_file, 'r') as cf:
            try:
                memory = json.load(cf)
            except:
                memory = {}

        memory_key = "" if not args.title else f"{args.title.lower()}{PART_SEPARATOR}{(args.artist or '').lower()}"
        artist = memory.get(memory_key, {}).get('artist', args.artist) if not args.forget else args.artist
        title = memory.get(memory_key, {}).get('name', args.title) if not args.forget else args.title

        uri = memory.get(memory_key, {}).get('uri')

        tracks = enqueue(
            title=title,
            artist=artist,
            times=args.times,
            last=args.previous,
            group=args.group,
            uri=uri
        )

        if args.remember and len(tracks or []) == 1: 
            print(
                f"Creating shortcut for {tracks[0].get('name')} by {tracks[0].get('artist')}: ", 
                f"'{args.remember[0]}'", 
                f"'{args.remember[1]}'" if len(args.remember) > 1 else ''
            )
            remember_track(
                args.remember[0], 
                args.remember[1] if len(args.remember) > 1 else None, 
                tracks[0]
            )

if __name__ == '__main__':
    queue_track()    