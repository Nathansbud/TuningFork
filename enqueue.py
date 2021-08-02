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
def load_groups():
    if not os.path.isfile(group_file):
        with open(group_file, 'w+') as gf: json.dump({}, gf)
    
    with open(group_file, 'r') as gf: 
        return json.load(gf)

spotify = get_token()
groups = load_groups()

def get_track(uri):
    if not uri: return
    uri = uri.strip()

    idx = uri if ':' not in uri else uri[uri.rindex(':')+1:]
    resp = spotify.get(f'https://api.spotify.com/v1/tracks/{idx}').json()
    if resp:
        return {
            'uri': resp.get('uri'),
            'name': resp.get('name'),
            'artist': ", ".join([artist.get('name') for artist in resp.get('artists')])
        }

def current(): return spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json().get('item', {})
def current_uri(): current().get('uri')
def current_lyrics():
    current_track = current()
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
        
        return "No lyrics found!"
    
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
            
            
def enqueue(title=None, artist=None, times=1, last=None, group=None):
    track_uris = []
    group_data = []    
    if group:
        with open(group_file) as gf:
            try:
                groups = json.load(gf)
            except json.JSONDecodeError:
                groups = {}
        
        group_data = groups.get(group, [])
        track_uris = [t.get('uri') for t in group_data] 
        
    elif title: 
        if artist:
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}%20artist:{artist}&type=track&limit=1&offset=0").json()
        else: 
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}&type=track&limit=1&offset=0").json()

        track_uris = [st['tracks']['items'][0]['uri']] if st['tracks']['items'] else []
    elif last:
        previous = spotify.get(f"https://api.spotify.com/v1/me/player/recently-played?limit={last}").json()
        track_uris = [s.get('track', {}).get('uri') for s in previous.get('items')][::-1]
    else:
        current = spotify.get("https://api.spotify.com/v1/me/player/currently-playing")
        if current.status_code == 204: 
            print("No track currently playing!")
        else:
            data = current.json().get('item', {})
            track_uris = [data.get('uri')]
            group_data = [{'name': data.get('name'), 'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])])}]

    if track_uris:
        for i in range(times):  
           for uri in track_uris:
               spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={uri}")

        if last:
            print(f"Added{' ' + str(last) if last > 1 else ''} last played item{'s' if last > 1 else ''} to queue {times}x!")
        elif group or not title:
            print("Added " + ", ".join([f"{t.get('name')} by {t.get('artist')}" for t in group_data]) + f" to queue {times}x!")
        # elif not title:
        #     print(f"Added currently playing track to queue {times}x!")
        else:
            print(f"Added {title.strip()} to queue {times}x!")
    else:
        print("Could not find track(s)!")

def queue_track():
    parser = argparse.ArgumentParser(description="Spotify track queuer")

    parser.add_argument('title', nargs='?', default=None)
    parser.add_argument('artist', nargs='?', default=None)

    #This arg achieves nothing, I just want queue and queue -c to do the same thing
    parser.add_argument('-c', '--current', action="store_true")

    parser.add_argument('-t', '--times', default=1, type=int)
    parser.add_argument('-p', '--previous', default=0, type=int)
    
    parser.add_argument('-l', '--list_groups', action='store_true')
    parser.add_argument('-a', '--add_group', action='store_true')
    parser.add_argument('-d', '--delete_group')
    parser.add_argument('-g', '--group', type=str)

    args = parser.parse_args()
    if args.add_group: add_group()
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
        enqueue(
            title=args.title,
            artist=args.artist,
            times=args.times,
            last=args.previous,
            group=args.group
        )

if __name__ == '__main__':
    queue_track()    