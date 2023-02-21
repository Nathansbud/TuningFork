from time import sleep
import webbrowser
from utilities import (
    search, get_token, 
    SongParser, SongException,
    color, Colors
)

import os
import json
import argparse
import shlex
import random
from itertools import permutations
from sys import argv

from scraper import get_lyrics
from lastly import get_current_track

group_file = os.path.join(os.path.dirname(__file__), "resources", "groups.json")
short_file = os.path.join(os.path.dirname(__file__), "resources", "shortcuts.json")
prefs_file = os.path.join(os.path.dirname(__file__), "resources", "preferences.json")

PART_SEPARATOR = '<--|-->'

def load_prefs():
    if not os.path.isfile(group_file):
        with open(group_file, 'w+') as gf: json.dump({}, gf)

    if not os.path.isfile(prefs_file):              
        with open(prefs_file, 'w+') as gf: json.dump({"DEFAULT_PLAYLIST": None}, gf)
    
    with open(group_file, 'r') as gf, open(prefs_file, 'r') as pf: 
        return json.load(gf), json.load(pf)


spotify = get_token()
groups, prefs = load_prefs()

def get_track(uri, formatted=True):
    if not uri: return [{}]
    uri = uri.strip()
    idx = uri if ':' not in uri else uri[uri.rindex(':')+1:]
    if ':album:' in uri:
        album_data = spotify.get(f'https://api.spotify.com/v1/albums/{idx}').json()
        album_tracks = spotify.get(f'https://api.spotify.com/v1/albums/{idx}/tracks?limit=50').json()
        return [{
            'name': t.get('name'), 
            'artist': ', '.join([artist.get('name') for artist in t.get('artists', [])]),
            'uri': t.get('uri'), 
            'album': album_data.get('name'),
            'album_uri': album_data.get('uri')
        } for t in album_tracks.get('items', [])]
    else:
        resp = spotify.get(f'https://api.spotify.com/v1/tracks/{idx}').json()
        if resp and formatted:
            return [{
                'uri': resp.get('uri'),
                'name': resp.get('name'),
                'artist': ", ".join([artist.get('name') for artist in resp.get('artists')]),
                'album': resp.get("album", {}).get('name'),
                'album_uri': resp.get("album", {}).get('uri')
            }]
        
        return resp

def current(): return spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json().get('item', {})
def current_uri(): return current().get('uri')
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
    
def make_group():
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
                if args.title: track = get_track(search(args.title, args.artist, spotify))[0]
                elif args.uri: track = get_track(args.uri)[0]
                elif args.current: track = get_track(current_uri())[0]
                else:
                    raise SongException("Invalid track specifier! Provide artist (and track), else specify current (-c) or uri (-u)!")

                if track:
                    confirm = input(f"Found track: {track.get('name')} by {track.get('artist')}. Add to group {name} (y/n)? ").lower().strip()
                    if confirm == 'y': tracks.append(track)
                else: 
                    print("Could not find a matching track!")

            except SongException as e:
                print(e)
            
            
def enqueue(title=None, artist=None, times=1, last=None, group=None, uri=None, ignore=False, mode="tracks"):
    group_data = []   
    tracks = []
    
    if group:
        with open(group_file) as gf:
            try:
                groups = json.load(gf)
            except json.JSONDecodeError:
                groups = {}
        
        group_data = groups.get(group, [])
        tracks = group_data
    elif title or uri: 
        if uri: tracks = get_track(uri, True)
        else:
            if artist:
                st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}%20artist:{artist}&type={mode[:-1]}&limit=1&offset=0").json()
            else: 
                st = spotify.get(f"https://api.spotify.com/v1/search/?q={title}&type={mode[:-1]}&limit=1&offset=0").json()
            
            data = st[mode]['items'][0] if st[mode]['items'] else {}
        
            if mode == "albums" and data:
                track_data = spotify.get(f'https://api.spotify.com/v1/albums/{data.get("uri").split(":")[-1]}/tracks?limit={data.get("total_tracks")}').json()
                tracks = [{
                    'name': t.get('name'), 
                    'artist': ', '.join([artist.get('name') for artist in t.get('artists', [])]),
                    'album': data.get('name'),
                    'uri': t.get('uri'),
                    'album_uri': data.get('uri')
                } for t in track_data.get('items', [])]
            else:
                tracks = [{
                    'name': data.get('name'), 
                    'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
                    'album': data.get('album'),
                    'uri': data.get('uri')
                }] if data else []
    elif last:
        previous = spotify.get(f"https://api.spotify.com/v1/me/player/recently-played?limit={last}").json()
        responses = [s.get('track', {}) for s in previous.get('items', [])][::-1]
        if mode != "tracks": 
            print("Can only re-queue tracks, not albums!")
            exit(0)
        else:
            tracks = [{
                'name': data.get('name'),
                'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
                'uri': data.get('uri'),
                'album': data.get('album'),
                'album_uri': data.get('uri'),
            } for data in responses]
    else:
        current = spotify.get("https://api.spotify.com/v1/me/player/currently-playing")
        
        if current.status_code == 204: 
            print("No track currently playing!")
            tracks = []
        else:
            data = current.json().get('item', {})
            if mode == 'albums':
                album = data.get("album")
                track_data = spotify.get(f'https://api.spotify.com/v1/albums/{album.get("uri").split(":")[-1]}/tracks?limit={album.get("total_tracks")}').json()
                tracks = [{
                    'name': t.get('name'), 
                    'artist': ', '.join([artist.get('name') for artist in t.get('artists', [])]),
                    'uri': t.get('uri'),
                    'album': album.get('name'),
                    'album_uri': album.get("uri")
                } for t in track_data.get('items', [])]
            else:
                tracks = [{
                    'name': data.get('name'), 
                    'artist': ', '.join([artist.get('name') for artist in data.get('artists', [])]),
                    'uri': data.get('uri'),
                    'album': data.get('album', {}).get("name"),
                    'album_uri': data.get('album', {}).get("uri"),
                }]

    if ignore: return tracks
    elif tracks:
        if last:
            print(f"""Adding{' ' + str(last) if last > 1 else ''} last played item{'s' if last > 1 else ''} ({', '.join([f"{t.get('name')} by {t.get('artist')}" for t in tracks])}) to queue {times}x!""")
        elif mode == 'tracks':
            print("Adding " + ", ".join([
                f"{color(t.get('name'), Colors.CYAN)} by {color(t.get('artist'), Colors.GREEN)}" for t in tracks
            ]) + f" to queue {times}x!")
        elif mode == 'albums':
            print(f"Adding album {tracks[0].get('album')} by {tracks[0].get('artist')} ({len(tracks)} tracks) to queue {times}x!")
            # build in a bit of time to cancel, because adding the wrong album is a pain in the butt
            sleep(2)

        for _ in range(times):  
            for t in tracks:
                response = spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={t.get('uri')}")
                if response.status_code >= 300: 
                    print(f"Failed to add {t.get('name')} by {t.get('artist')} to queue (status code: {response.status_code})")

        return tracks
    else:
        print("Could not find track(s)!")

def remember_track(title, artist, track, mode, delete=False):
    memory = {"albums": {}, "tracks": {}}
    if os.path.isfile(short_file):
        with open(short_file, "r") as cf:
            try: 
                memory = json.load(cf)
            except:
                memory = {
                    "albums": {},
                    "tracks": {}
                }
    
    mem_key = f"{(title or '').lower()}{PART_SEPARATOR}{(artist or '').lower()}"

    if delete: 
        if mem_key in memory[mode]: del memory[mode][mem_key]
        else: 
            print(f"Could not find any existing shortcuts for {title}{'by ' + artist if artist else ''}!")
    elif track:
        memory[mode][mem_key] = {
            'name': track.get('name'), 
            'artist': track.get('artist'),
            'album': track.get('album'),
            'relevant_uri': track.get('uri') if mode == 'tracks' else track.get('album_uri')
        }
    else:
        print("New shortcuts must have a track or album!")

    with open(short_file, "w+") as wf:
        json.dump(memory, wf)


def queue_track():
    parser = argparse.ArgumentParser(description="Spotify track queuer")

    parser.add_argument('title', nargs='?', default=None)
    parser.add_argument('artist', nargs='?', default=None)

    parser.add_argument('-a', '--album', action="store_true")
    
    parser.add_argument('-i', '--ignore', action='store_true')      

    parser.add_argument('-o', '--open', action="store_true")
    parser.add_argument('-c', '--song', action="store_true")

    parser.add_argument('-s', '--save', action='store_true')
    parser.add_argument('-z', '--watch', action='store_true')
    
    parser.add_argument('-x', '--source', nargs="?", const="LIBRARY")
    parser.add_argument('-#', '--offset', type=int)

    parser.add_argument('-u', '--uri', default=None)

    parser.add_argument('-t', '--times', nargs='?', default=1, const=1, type=int)
    parser.add_argument('-p', '--previous', nargs='?', const=1, type=int)
    
    parser.add_argument('-l', '--list_rules', action='store_true')
    
    parser.add_argument('-m', '--make_group', action='store_true')
    parser.add_argument('-d', '--delete_group')
    parser.add_argument('-g', '--group', type=str)

    parser.add_argument('-r', '--remember', nargs='*', default=None)
    parser.add_argument('-f', '--forget', nargs='*', default=None)
    parser.add_argument('-n', '--amnesia', action='store_true')

    parser.add_argument('-w', '--which', action='store_true')

    parser.add_argument('-st', '--spaced_track', nargs='*', default=None)
        
    args = parser.parse_args()
    if args.spaced_track: args.title = " ".join(args.spaced_track)

    mode = "tracks" if (not args.album and not args.source) else "albums"
    if args.source:
        source = args.source.upper()
        if source not in ["LIBRARY", "BACKLOG"]: 
            print("Source must be one of: LIBRARY, BACKLOG")
            exit(1)
        
        idx = args.offset or -1
        if source == "BACKLOG" and prefs.get("ALBUM_PLAYLIST"):            
            count = spotify.get(f"https://api.spotify.com/v1/playlists/{prefs.get('ALBUM_PLAYLIST')}/tracks").json().get('total')
            if not count > idx > -1:
                print(f"Choosing a random backlog album from the {count} available...")
                idx = random.randint(0, count - 1)
            else:
                idx = count - idx
            
            chosen = spotify.get(f"https://api.spotify.com/v1/playlists/{prefs.get('ALBUM_PLAYLIST')}/tracks?limit=1&offset={idx}").json()
            found_album = chosen.get("items")[0].get("track").get("album")
            args.uri = found_album.get("uri")
            if not args.uri: 
                print(f"Can't queue album {idx}; {found_album.get('name')} is hosted locally, and can't be queued via API!")
                exit(0)

        elif source == "LIBRARY":
            count = spotify.get("https://api.spotify.com/v1/me/albums?limit=1&offset=0").json().get('total')
            if not count > idx > -1:
                print(f"Choosing a random library album from the {count} available...")
                idx = random.randint(0, count - 1)

            chosen = spotify.get(f"https://api.spotify.com/v1/me/albums?limit=1&offset={idx}").json()
            args.uri = chosen.get("items")[0].get("album").get("uri")
        else:
            print("Could not locate an album backlog playlist; try adding an ALBUM_PLAYLIST key to preferences.json?")
            exit(1)

    if args.forget: 
        print(
            f"Deleting shortcut:", 
            f"'{args.forget[0]}'", 
            f"'{args.forget[1]}'" if len(args.forget) > 1 else ''
        )
        
        remember_track(
            args.forget[0], 
            args.forget[1] if len(args.forget) > 1 else None, 
            None,
            mode,
            delete=True
        )
    elif args.which:
        cs = spotify.get("https://api.spotify.com/v1/me/player/currently-playing")
        if cs.status_code == 204: 
            print("No track currently playing!")
        else:
            playing = cs.json().get('item', {})
            print(f"{color(playing.get('name'), Colors.CYAN)} by {color(', '.join([artist.get('name') for artist in playing.get('artists', [])]), Colors.GREEN)}")
    elif args.make_group: make_group()
    elif args.delete_group: 
        with open(group_file, 'r+') as gf:
            try:
                groups = json.load(gf)
                if args.delete_group in groups: 
                    del groups[args.delete_group]
                    print(f"Deleting group {args.delete_group}...")
                    sleep(2)
                    
                else: print(f"Group {args.delete_group} not found!")
            except json.JSONDecodeError:
                print("No groups found!")
                groups = {}
        
        with open(group_file, 'w+') as gf:
            json.dump(groups, gf)

    elif args.list_rules: 
        with open(group_file, 'r') as gf:
            try:
                groups = json.load(gf)
                if groups:
                    print(f"[{color('Saved Groups', Colors.CYAN)}]\n")
                    for name, data in groups.items():
                        tracks = "\n".join([
                            f"\t{i}. {color(d.get('name'), Colors.GREEN)} by {color(d.get('artist'), Colors.GREEN)} [{color(d.get('uri'), Colors.YELLOW)}]" 
                            for i, d in enumerate(data, start=1)
                        ])
                        print(f"{color(name, Colors.MAGENTA)}: {tracks}\n")
                        
                    print()
            except json.JSONDecodeError:
                pass

        if os.path.isfile(short_file): 
            with open(short_file, 'r') as cf:
                try: 
                    shortcuts = json.load(cf)
                    tracks, albums = shortcuts.get('tracks'), shortcuts.get('albums')
                    for title, ss in [("Track Shortcuts", tracks), ("Album Shortcuts", albums)]:
                        if ss:
                            print(f"[{color(title, Colors.CYAN)}]\n")
                            for r in sorted([[
                                color(", ".join(key.split(PART_SEPARATOR)), Colors.MAGENTA),
                                "->",
                                f"{color(track.get('name' if mode == 'tracks' else 'album'), Colors.GREEN)} by {color(track.get('artist'), Colors.GREEN)}",
                                f"[{color(track.get('relevant_uri', track.get('uri')), Colors.YELLOW)}]"
                            ] for key, track in ss.items()], key=lambda l: l[2].lower()):
                                print(*r)
                        print()

                except json.JSONDecodeError:
                    pass

    else:
        with open(short_file, 'r') as cf:
            try:
                memory = json.load(cf)
            except:
                memory = {"tracks": {}, "albums": {}}

        memory_key = "" if not args.title else f"{args.title.lower()}{PART_SEPARATOR}{(args.artist or '').lower()}"
        
        mobject = memory.get(mode, {}).get(memory_key, {})
        
        artist = mobject.get('artist', args.artist) if not args.amnesia else args.artist
        title = mobject.get('name', args.title) if not args.amnesia else args.title

        uri = args.uri or mobject.get('uri') or mobject.get('relevant_uri')
        tracks = enqueue(
            title=title,
            artist=artist,
            times=args.times,
            last=args.previous,
            group=args.group,
            uri=uri,
            ignore=args.ignore or args.open,
            mode=mode
        )

        if args.remember and tracks: 
            if len(args.remember) == 0:
                print("Cannot create a shortcut without any arguments!")
            else:
                print(
                    f"Creating shortcut for {mode[:-1]} {tracks[0].get('name' if mode == 'tracks' else 'album')} by {tracks[0].get('artist')}: ", 
                    f"'{args.remember[0]}'", 
                    f"'{args.remember[1]}'" if len(args.remember) > 1 else ''
                )
                
                remember_track(
                    args.remember[0], 
                    args.remember[1] if len(args.remember) > 1 else None, 
                    tracks[0],
                    mode
                )

        if args.watch:
            track = get_current_track(prefs.get("LASTFM_WATCH_USER"))
            if track:
                if args.save and prefs.get("SHARED_PLAYLIST"):
                    uri = search(track["title"], track["artist"], spotify)
                    resp = spotify.post(f"https://api.spotify.com/v1/playlists/{prefs.get('SHARED_PLAYLIST')}/tracks?uris={uri}")
                    if 200 <= resp.status_code < 300:
                        print(f"Added {color(track.get('title'), Colors.CYAN)} by {color(track.get('artist'), Colors.GREEN)} to shared playlist!")
                    else:
                        print(f"Something went wrong while adding to shared playlist (status code {resp.status_code})")
                elif not prefs.get("SHARED_PLAYLIST"):
                    print("Could not find a SHARED_PLAYLIST to add song to; try adding one to preferences.json?")
                else:
                    print(f"{color(prefs.get('LASTFM_WATCH_USER'), Colors.YELLOW)} is listening to {color(track.get('title'), Colors.CYAN)} by {color(track.get('artist'), Colors.GREEN)}!")
            else:
                print("Could not find a valid LASTFM_WATCH_USER to save track from; try adding one to preferences.json?")
        elif args.save:
            if prefs.get("DEFAULT_PLAYLIST"):
                track_uris = [t.get("uri") for t in tracks if t.get("uri")]
                if len(track_uris) > 0:
                    resp = spotify.post(f"https://api.spotify.com/v1/playlists/{prefs.get('DEFAULT_PLAYLIST')}/tracks?uris={','.join(track_uris)}")
                    if 200 <= resp.status_code < 300:
                        print(f"Added {', '.join(t.get('name') for t in tracks)} to playlist!")
                    else:
                        print(f"Something went wrong while adding to playlist (status code {resp.status_code})")
                else:
                    print("No tracks found!")
            else: 
                print("Could not locate a default playlist; try adding a DEFAULT_PLAYLIST key to preferences.json?")

        if args.open:
            if prefs.get("LASTFM_USER"):
                artist_fmt = lambda t: t.get("artist").replace(" ", "+").split(",")[0]

                track_artists = set(artist_fmt(t) for t in tracks)
                track_albums = set((artist_fmt(t), t.get("album").replace(" ", "+")) for t in tracks)
                track_songs = set((artist_fmt(t), t.get("name").replace(" ", "+")) for t in tracks)

                user = prefs.get("LASTFM_USER")
                if args.song:
                    for art, s in track_songs:
                        webbrowser.open(f"https://www.last.fm/user/{user}/library/music/{art}/_/{s}")
                elif args.album:
                    for art, alb in track_albums:
                        webbrowser.open(f"https://www.last.fm/user/{user}/library/music/{art}/{alb}")
                else:
                    for t in track_artists:
                        webbrowser.open(f"https://www.last.fm/user/{user}/library/music/{t}")
            else:
                print("Could not find a Last.fm username; try adding one to preferences.json?")

if __name__ == '__main__':
    try:
        queue_track()
    except KeyboardInterrupt:
        exit(0)
