import argparse
import json
import os
import random
import shlex
import webbrowser
from datetime import datetime, timedelta
from time import sleep

from lastly import get_current_track, get_top_tracks
from model import AlbumObject, TrackObject
from scraper import get_lyrics
from network import client as spotify
from utilities import (
    album_format, track_format, extract_id,
    get_share_link, send_message_to_user,
    dropdown,
    SongParser, SongException,
    red, green, yellow, blue, magenta, cyan, white, bold, rainbow, 
)

group_file = os.path.join(os.path.dirname(__file__), "resources", "groups.json")
short_file = os.path.join(os.path.dirname(__file__), "resources", "shortcuts.json")
prefs_file = os.path.join(os.path.dirname(__file__), "resources", "preferences.json")

PART_SEPARATOR = '<--|-->'

def load_prefs():
    if not os.path.isfile(group_file):
        with open(group_file, 'w+') as gf: json.dump({}, gf)

    if not os.path.isfile(prefs_file):              
        with open(prefs_file, 'w+') as gf: json.dump({
                "PLAYLISTS": {
                    "DEFAULT": "",
                    "PRIMARY": "",
                    "BACKLOG": "",
                    "SHARED": ""
                },
                "ALIASES": {},
                "LASTFM_USER": "",
                "LASTFM_WATCH_USER": "Nathansbud"
            })

    with open(group_file, 'r') as gf, open(prefs_file, 'r') as pf: 
        try:
            gs = json.load(gf)
        except Exception: 
            gs = {}
        
        try: 
            ps = json.load(pf)
        except Exception:
            ps = {}
        
        return gs, ps

groups, prefs = load_prefs()

def playlist_name(pid):
    playlist_data = spotify.get(f"https://api.spotify.com/v1/playlists/{pid}")
    if playlist_data.status_code == 200: 
        return playlist_data.json().get('name')
    else:
        return None 

def playlist_id(identifier):
    if identifier.startswith('http'):
        return identifier.split("/")[-1].split("?")[0]
    elif identifier.startswith("spotify:playlist:"):
        return identifier.split(":")[-1]
    else:
        return prefs.get("PLAYLISTS", {}).get(identifier.upper())

def text_recipient(alias):
    return prefs.get("ALIASES", {}).get(alias.upper())

def make_group():
    tracks = []
    name = input(blue("Group Name: "))
    
    parser = SongParser("Song Parser")
    parser.add_argument('title', nargs="?")
    parser.add_argument('artist', nargs="?")
    parser.add_argument('-c', '--current', action='store_true')
    parser.add_argument('-u', '--uri')

    print(f"Specify title + artist, currently playing (-c), or URI (-u). Type {magenta('SAVE')} when finished!")
    sleep(0.5)
    adding = True
    
    while adding:
        candidate_track = input(magenta(f"Item {len(tracks) + 1}: "))
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
                if args.title: track = spotify.search(args.title, args.artist)
                elif args.uri: track = spotify.get_track(extract_id(args.uri))
                elif args.current: track = spotify.get_current_track()
                else:
                    raise SongException("Invalid track specifier! Provide artist (and track), else specify current (-c) or uri (-u)!")

                if track:
                    confirm = input(f"Found track: {track.prettify(album=True)}. Add to group {blue(name)} ({bold('y/n')})? ").lower().strip()
                    if confirm == 'y': tracks.append(shortcut_serialize(track))
                else: 
                    print("Could not find a matching track!")

            except SongException as e:
                print(e)

def enqueue(
    title=None, 
    artist=None, 
    times=1,
    last=None, 
    group=None, 
    user=None, 
    uri=None,
    ignore=False, 
    mode="tracks", 
    limit=None
):
    if not limit: limit = []

    group_data = []   
    tracks = []
    
    if group:
        with open(group_file) as gf:
            try:
                groups = json.load(gf)
            except json.JSONDecodeError:
                groups = {}
        
        group_data = groups.get(group, [])
        if not group_data:
            print(f"Could not find group {blue(group)}; try creating via {magenta('--make_group')}!")
            return [], 404

        tracks = [shortcut_deserialize(item) for item in group_data]
    elif user:
        track_data = get_top_tracks(start_date=datetime.now() - timedelta(days=365), end_date=datetime.now(), user=user, limit=max(50, times))
        tracks = [{"uri": spotify.search(td['name'], td['artist']), **td} for td in random.sample(track_data, times)]
        # we can't use times with this flag!
        if times > 0: 
            times = 1
    elif title or uri: 
        if uri:
            idx, is_album = extract_id(uri)
            if is_album: mode = 'albums'

            tracks = [spotify.get_track(idx)] if not is_album else spotify.get_album(idx).tracks
        else:
            result = spotify.search(title, artist, mode[:-1])
            if result:
                tracks = [result] if mode == "tracks" else spotify.get_album(result.id).tracks
            
    elif last:
        if mode != "tracks": 
            print("Can only re-queue tracks, not albums!")
            exit(0)

        tracks = spotify.get_recent_tracks(last)
    else:
        current = spotify.get_current_track()
        if not current:
            print("No track currently playing!")
            exit(1)
        else:
            tracks = [current] if mode == 'tracks' else spotify.get_album_tracks(album=current.album)

    if not tracks:
        print("Could not find track(s)!")
        return [], 404
    elif ignore:
        return tracks, 200

    og = len(tracks)
    
    limiter = slice(
        max(0, limit[0] - 1) if len(limit) > 0 else 0, 
        max(1, limit[1]) if len(limit) > 1 else len(tracks)
    )

    tracks = tracks[limiter]

    if last:
        print(f"Adding {bold(last)} last played item(s) ({', '.join([t.prettify() for t in tracks])}) to queue {bold(f'{times}x')}!")
    elif mode == 'tracks':
        print(f"Adding {', '.join([t.prettify() for t in tracks])} to queue {bold(f'{times}x')}!")
    elif mode == 'albums':
        lr = f"track {limiter.stop}" if limiter.start + 1 == limiter.stop else f"tracks {limiter.start + 1} through {limiter.stop}"
        nt = f'{len(tracks)} tracks' if og == len(tracks) else f'{lr}'
        
        print(f"Adding album {tracks[0].album.prettify()} ({bold(nt)}) to queue {bold(f'{times}x')}!")
        # build in a bit of time to cancel, because adding the wrong album is a pain in the butt
        sleep(2)

    status = 200
    for _ in range(times):  
        for t in tracks:
            if not spotify.queue(t.uri):
                print(f"Failed to add {t.prettify()} to queue!")
                
    return tracks, status

def shortcut_serialize(obj: AlbumObject | TrackObject):
    return {
        'name': obj.name, 
        'artist': obj.artist,
        'album': obj.name if isinstance(obj, AlbumObject) else obj.album.name,
        'uri': obj.uri
    }

def shortcut_deserialize(obj: dict, is_album=False):
    shared = {
        "name": obj.get('name'),
        "artist": obj.get('artist'),
        "uri": obj.get('uri'),
        "id": extract_id(obj.get('uri'))
    }

    if is_album: return AlbumObject(**shared)
    else:
        return TrackObject(**shared)

def remember_track(title, artist, track, mode, limit=None, delete=False):
    memory = {"albums": {}, "tracks": {}}
    if os.path.isfile(short_file):
        with open(short_file, "r") as cf:
            try: 
                memory = json.load(cf)
            except Exception:
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
            **shortcut_serialize(track),
            'limit': limit or []
        }
    else:
        print("New shortcuts must have a track or album!")

    with open(short_file, "w+") as wf:
        json.dump(memory, wf)

def progress_playlist(playlist_id):
    track_uri, metadata = spotify.get_playlist_tracks(
        playlist_id=playlist_id,
        limit=1
    )[0]
    
    _, status = enqueue(uri=metadata['track']['album']['uri'], mode="albums")
    if status == 200:
        spotify.remove_playlist_tracks(playlist_id, track_uris=[track_uri])

def queue_track():
    parser = argparse.ArgumentParser(description=f"{magenta('Enqueue')}: {green('Spotify')} {bold('Queue Manager')}!")

    parser.add_argument('title', nargs='?', default=None)
    parser.add_argument('artist', nargs='?', default=None)
    parser.add_argument('-u', '--uri', default=None, help="Queue Spotify URI")
    parser.add_argument('-c', '--song', action="store_true", help="Queue current song")
    parser.add_argument('-a', '--album', nargs='*', type=int, const=None, help="Queue album by title rather than song")
    parser.add_argument('-g', '--group', type=str, help="Queue group name")
    parser.add_argument('-st', '--spaced_track', nargs='*', default=None, help="Treat positional arguments as song title")

    parser.add_argument('-q', '--queue', action='store_true', help="Print current play queue")
    parser.add_argument('-w', '--which', action='store_true', help="Print currently playing track")
    parser.add_argument('-n', '--next', nargs='?', const=1, type=int, help="Skip the next n tracks")
    
    parser.add_argument('--pause', action='store_true', help='Pause playback')
    parser.add_argument('--playpause', action='store_true', help="Resume or pause playback")
    parser.add_argument('-v', '--volume', nargs='?', const=0, type=int, help="Set volume level")

    parser.add_argument('-x', '--source', choices=["LIBRARY", "BACKLOG"], nargs="?", type=lambda s: s.upper(), const="LIBRARY", help="Queue from source")
    parser.add_argument('-#', '--offset', nargs="+", type=int, help="Queue offset within source")

    parser.add_argument('-y', '--progress', action="store_true")

    parser.add_argument('-t', '--times', nargs='?', default=1, const=1, type=int, help="Times to repeat request action")
    parser.add_argument('--previous', nargs='?', const=1, type=int, help="Queue previous n tracks")
    
    parser.add_argument('-z', '--watch', nargs='?', const=prefs.get("LASTFM_WATCH_USER", ""), type=str, help="Queue most recent track from provided last.fm user (default: LASTFM_WATCH_USER preference)")
    parser.add_argument('-@', '--user', nargs='?', const=prefs.get("LASTFM_USER", ""), type=str, help="Queue random top track from provided last.fm user (default: LASTFM_USER preference)"), 
    parser.add_argument('-m', '--lastfm', nargs='?', const=prefs.get("LASTFM_USER", ""), type=str, help="Open the artist/album in library page of provided last.fm user (default: LASTFM_USER preference)")
    parser.add_argument('-o', '--spotify', action="store_true", help="Open current album in Spotify")
    
    parser.add_argument('-r', '--remember', nargs='*', default=None, help="Create custom rule for queue behavior")
    parser.add_argument('-f', '--forget', nargs='*', default=None, help="Delete custom rule for queue behavior")
    parser.add_argument('--list_rules', action='store_true', help="List all created custom rules for queue behavior")
    parser.add_argument('--amnesia', action='store_true', help="Queue ignoring custom rules")

    parser.add_argument('-s', '--save', nargs="*", type=lambda s: s.upper(), help="Save queue set to playlist specified in preferences")
    parser.add_argument('-p', '--playlist', nargs="?", const="PRIMARY", type=lambda s: s.upper(), help="Move playback to a playlist specified in preferences")
    parser.add_argument('-l', '--like', action='store_true', help="Add queue set to Liked Songs")

    parser.add_argument('--share', choices=["SPOTIFY", "APPLE"], nargs="?", type=lambda s: s.upper(), const="SPOTIFY", help="Copy queued link to share")
    parser.add_argument('--text', nargs="*", help="Recipients to send share text")

    parser.add_argument('--make_group', action='store_true', help="Create custom named group of items to queue together")
    parser.add_argument('--delete_group', help="Delete custom named group")
    
    parser.add_argument('-i', '--ignore', action='store_true', help="Ignore the request to queue (e.g. if trying to save a rule)")      

    args = parser.parse_args()
    if args.spaced_track: args.title = " ".join(args.spaced_track)  
    
    # if --save, args.save == [], else it will be None
    if not args.save: args.save = ["DEFAULT"] if isinstance(args.save, list) else []
    
    save_to = {p: playlist_id(p) for p in args.save}
    recipients = [(t, text_recipient(t)) for t in (args.text or []) if t]
    
    if args.pause or args.playpause:
        success, paused = spotify.playpause(args.pause)
        if not success:
            print("Could not communicate with an active device; try manually playing/pausing instead!")
        else:
            print(f'{yellow("Pausing") if paused else yellow("Resuming")} {bold("playback...")}')

        exit(0)
        
    elif args.volume is not None:
        try: 
            if spotify.set_volume(args.volume):
                print(f"Successfully set {magenta('device volume level')} to " + bold(f"{args.volume}%") + "!")
            else:
                print(f"Unfortunately, the current device {red('does not allow')} programmatic volume changes!")     
        except ValueError:
            print(f"{magenta('Volume level')} must be a value from {bold('0–100')}!")

        exit(0)

    mode = "tracks" if (args.album is None and not args.source) else "albums"
    if args.queue:
        # Finally, a queue endpoint exists...it doesn't differentiate between Queue vs Up Next, but we will mf take it
        active_queue = spotify.get_queue()
        if len(active_queue) == 0: print("No track currently playing!")
        else:
            current = spotify.get_current_track()
            print(f"{magenta('C')}.\t{current.prettify(timestamp=True)}")
            
            # if the current track in the queue is local, current won't equal queue's currently_playing; 
            # there is currently no good solution for local tracks in the queue, alas
            for i, t in enumerate(active_queue[0 if current.local else 1:], start=1):
                print(f"{magenta(i)}.\t{t.prettify()}")
        
        exit(0)
    elif args.next and args.next > 0:
        print(f"Attempting to skip {bold(f'{args.next} track(s)')}...")
        # This is probably not the optimal way to do this...but if we get rate limited, so be it
        if spotify.skip(times=args.next) == 404:
            print("No track currently playing!")
            exit(1)
       
        # Spotify API takes a second to catch up, so we need to sleep before hitting current track endpoint, 
        # since next doesn't return track info
        sleep(1)
        print(f"Now playing: {spotify.get_current_track().prettify(album=True, timestamp=False)}!")
        exit(0)
    elif args.playlist:
        puri = playlist_id(args.playlist)
        if puri:
            play_name = playlist_name(puri)
            req_p = spotify.put(f"https://api.spotify.com/v1/me/player/play", data=json.dumps({
                "context_uri": f"spotify:playlist:{puri}",
            }))

            if not 200 <= req_p.status_code < 300:
                print(f"Failed to transfer playlist to {magenta(args.playlist)}, double check your preferences or try again later!")
            else:
                print(f"Transferred playback to playlist: {magenta(play_name)} ({magenta(args.playlist)})!")
        else:
            print(f"Cannot restore playback to playlist {magenta(args.playlist)}; try adding {magenta(args.playlist)} to your PLAYLISTS in preferences.json!")
        
        exit(0)

    if args.progress:
        if playlist_id("QUEUE"):
            progress_playlist(playlist_id("QUEUE"))
        else:
            print(f"Found no playlist {magenta('QUEUE')} to pop from; try adding one to your {magenta('PLAYLISTS')} in preferences.json!")
        
        exit(0)

    if args.source:
        if args.source not in ["LIBRARY", "BACKLOG"]: 
            print("Source must be one of: LIBRARY, BACKLOG")
            exit(1)
        
        idx = (args.offset[0] or -1) if args.offset else -1
        ran = args.offset[1] if args.offset and len(args.offset) > 1 else 1
        offset = 0

        backlog_uri = playlist_id("BACKLOG")
        if args.source == "BACKLOG" and backlog_uri:
            count = spotify.get(f"https://api.spotify.com/v1/playlists/{backlog_uri}/tracks").json().get('total')
            if not count > idx > -1:
                idx = random.randint(0, count - 1)
                if ran == 1:
                    print(f"Choosing a {rainbow('random')} backlog album from the {count} available...how about #{bold(idx)}?")
                else:
                    print(f"Choosing {bold(ran)} backlog albums from a {rainbow('random')} offset of the {count} available...#{bold(idx)}?")
            
            else:
                idx = count - idx
            
            chosen = spotify.get(f"https://api.spotify.com/v1/playlists/{backlog_uri}/tracks?limit={ran}&offset={idx - ran + 1}").json()
            if ran > 1:
                opts = {album_format(c.get("track"), use_color=False): c.get("track", {}).get('album', {}).get('uri') for c in reversed(chosen.get("items", []))}
                if len(opts) == 0:
                    print(f"Unfortunately, {bold(ran)} is more tracks than can be requested from {green('Spotify')} at once!")
                    exit(1)

                z, offset = dropdown(opts)
                if not z: exit(0) 
                # flip to account for non-reversed chosen
                offset = min(ran, len(chosen.get("items"))) - 1 - offset
            
            found_album = chosen.get("items")[offset].get("track").get("album")
            args.uri = found_album.get("uri")
            if not args.uri: 
                print(f"Can't queue album {idx}; {found_album.get('name')} is hosted locally, and can't be queued via API!")
                exit(0)

        elif args.source == "LIBRARY":
            count = spotify.get("https://api.spotify.com/v1/me/albums?limit=1&offset=0").json().get('total')
            if not count > idx > -1:
                idx = random.randint(0, count - 1)
                if ran == 1:
                    print(f"Choosing a {rainbow('random')} library album from the {count} available...how about #{bold(idx)}?")
                else:
                    print(f"Choosing {white(ran)} library albums from a {rainbow('random')} offset of the {count} available...#{bold(idx)}?")

            chosen = spotify.get(f"https://api.spotify.com/v1/me/albums?limit={ran}&offset={idx}").json()
            if ran > 1:
                opts = {album_format(c, use_color=False): c.get('album', {}).get('uri') for c in reversed(chosen.get("items", []))}
                if len(opts) == 0:
                    print(f"Unfortunately, {bold(ran)} is more albums than can be requested from {green('Spotify')} at once!")
                    exit(1)

                z, offset = dropdown(opts)
                if not z: exit(0) 
                # flip to account for non-reversed chosen
                offset = min(ran, len(chosen.get("items"))) - 1 - offset
            
            args.uri = chosen.get("items")[offset].get("album").get("uri")
        else:
            print(f"Could not locate an album backlog playlist; try adding a {magenta('BACKLOG')} to PLAYLISTS in preferences.json?")
            exit(1) 

    if args.forget: 
        print(
            f"Deleting shortcut:", 
            f"'{magenta(args.forget[0])}'", 
            f"'{magenta(args.forget[1])}'" if len(args.forget) > 1 else ''
        )
        
        remember_track(
            args.forget[0], 
            args.forget[1] if len(args.forget) > 1 else None, 
            None,
            mode,
            delete=True
        )
    elif args.which:
        current = spotify.get_current_track()
        if not current:
            print("No track currently playing!")
            exit(0)
        else:
            print(f"{bold('Now playing')}: {current.prettify(album=True, timestamp=True)}")
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
                    print(f"[{bold('Saved Groups')}]\n")
                    for name, data in groups.items():
                        tracks = "\n".join([
                            f"\t{i}. {track_format(d)} [{magenta(d.get('uri'))}]" 
                            for i, d in enumerate(data, start=1)
                        ])
                        print(f"{album_format(name)}: {tracks}\n")
                        
                    print()
            except json.JSONDecodeError:
                pass

        if os.path.isfile(short_file): 
            with open(short_file, 'r') as cf:
                try: 
                    shortcuts = json.load(cf)
                    tracks, albums = shortcuts.get('tracks'), shortcuts.get('albums')
                    for i, (title, ss) in enumerate([(green("Track Shortcuts"), tracks), (cyan("Album Shortcuts"), albums)]):
                        if ss:
                            print(f"[{title}]\n")
                            for r in sorted([[
                                magenta(", ".join(key.split(PART_SEPARATOR))),
                                "->",
                                track_format(track) if mode == 'tracks' else album_format(track),
                                f"[{magenta(track.get('relevant_uri', track.get('uri')))}]"
                            ] for key, track in ss.items()], key=lambda l: l[2].lower()):
                                print(*r)
                        print()

                except json.JSONDecodeError:
                    pass
    elif args.watch:
        track = get_current_track(args.watch)
        if track:
            shared_playlist = playlist_id("SHARED")
            if args.save: 
                if shared_playlist:
                    uri = spotify.search(track["name"], track["artist"])
                    resp = spotify.post(f"https://api.spotify.com/v1/playlists/{shared_playlist}/tracks?uris={uri}")
                    if 200 <= resp.status_code < 300:
                        print(f"Added {track_format(track)} to shared playlist!")
                    else:
                        print(f"Something went wrong while adding to shared playlist (status code {resp.status_code})")
                else:
                    print(f"Could not find playlist {magenta('SHARED')} under PLAYLISTS to add song to; try adding one to preferences.json?")
            else:
                print(f"{magenta(args.watch)} was last listening to {track_format(track)}!")
        else:
            print(f"Could not Last.fm username; watch takes a valid username, or uses preference {magenta('LASTFM_WATCH_USER')}!")
        
        exit(0)
    else:
        with open(short_file, 'r') as cf:
            try:
                memory = json.load(cf)
            except Exception:
                memory = {"tracks": {}, "albums": {}}

        memory_key = "" if not args.title else f"{args.title.lower()}{PART_SEPARATOR}{(args.artist or '').lower()}"
        
        mobject = memory.get(mode, {}).get(memory_key, {})
        
        artist = mobject.get('artist', args.artist) if not args.amnesia else args.artist
        title = mobject.get('name', args.title) if not args.amnesia else args.title
        limit = mobject.get('limit', []) if not (args.amnesia or args.album) else args.album

        uri = args.uri or mobject.get('uri')
        tracks, _ = enqueue(
            title=title,
            artist=artist,
            times=args.times,
            last=args.previous,
            group=args.group,
            user=args.user,
            uri=uri,
            ignore=any((args.ignore, args.lastfm is not None, args.spotify, args.save, args.like, args.share)),
            mode=mode,
            limit=limit
        )

        if (args.share or args.text) and tracks:
            if not args.share: args.share = "SPOTIFY"
            
            if mode == "albums":
                item = spotify.get(f"https://api.spotify.com/v1/albums/{tracks[0]['album_uri'].split(':')[-1]}").json()
            else:
                item = spotify.get(f"https://api.spotify.com/v1/tracks/{tracks[0]['uri'].split(':')[-1]}").json()
            
            res = get_share_link(item['external_urls']['spotify'], args.share != 'SPOTIFY')
            if res['code'] == 0 and len(res['link']) > 0:
                platform_render = magenta('Apple Music' if args.share != 'SPOTIFY' else 'Spotify')
                print(f"{bold('Copying')} {platform_render} share link for {album_format(item) if mode == 'albums' else track_format(item)} to clipboard!")

                # if we are about to text, build in a lil wait
                if recipients: sleep(2)

                for (r, number) in recipients:
                    print(f"{bold('Texting')} {platform_render} share link to {green(r)} ({number})")
                    if send_message_to_user(number, res['link']).get("code") != 0:
                        print(f"{red('Failed to send')}!")
            else:
                if args.share == "APPLE":
                    print(f"{red('Failed to copy to clipboard')}! This track may be named differently between platforms, or the required shortcut ({bold('https://tinyurl.com/yxwxw4ua')}) is not installed and named {bold('spotify-to-apple-music-link')}")
                elif res['code'] != 0:
                    print(f"{red('Failed to copy to clipboard')}!")

        if args.remember and tracks: 
            if len(args.remember) == 0:
                print("Cannot create a shortcut without any arguments!")
            else:
                lb, ub = (max(0, limit[0] - 1) if len(limit) > 0 else 0), (max(1, limit[1]) if len(limit) > 1 else len(tracks))

                print("".join([
                    f"Creating shortcut for {mode[:-1]} {tracks[0].prettify()}", 
                    ((bold(f" (track {lb})") if lb + 1 == ub else bold(f" (tracks {lb + 1} through {ub})")) if mode == 'albums' else '') + ": ",
                    f"'{magenta(args.remember[0])}'", 
                    f"'{magenta(args.remember[1])}'" if len(args.remember) > 1 else ''
                ]))
                
                remember_track(
                    args.remember[0], 
                    args.remember[1] if len(args.remember) > 1 else None, 
                    tracks[0],
                    mode,
                    args.album
                )

        if args.save:
            save_uris = set(save_to.values())
            if not (len(save_uris) == 1 and None in save_uris):
                for p, puri in save_to.items():
                    play_name = playlist_name(puri)
                    if not playlist_name:
                        print(f"Could not find playlist {p} from provided ID; make sure your preferences file has the correct ID ({bold('spotify:playlist:[id]')})!")
                        continue 
                    
                    if len(tracks) > 0:
                        if spotify.add_playlist_tracks(puri, tracks):
                            print(f"Added {', '.join(t.prettify() for t in tracks)} to {magenta(play_name)} ({magenta(p)})!")
                        else:
                            print(f"Something went wrong while adding to playlist {p}!")
                    else:
                        print("No tracks found!")
                        break
            else: 
                print("No valid playlists were provided; try adding one to PLAYLISTS in preferences.json")
        
        if args.like:
            if mode == 'tracks':
                liked = spotify.put("https://api.spotify.com/v1/me/tracks/", data=json.dumps({
                    "ids": [t.id for t in tracks]
                }))

                if 200 <= liked.status_code < 300:
                    print(f"Added {', '.join(t.prettify() for t in tracks)} to {magenta('Liked Songs')}!")
                else:
                    print(f"Something went wrong while adding to {magenta('Liked Songs')} (status code: {liked.status_code})")
            else:
                saved = spotify.put("https://api.spotify.com/v1/me/albums/", data=json.dumps({
                    "ids": [tracks[0].album.id]
                }))

                if 200 <= saved.status_code < 300:
                    print(f"Saved {tracks[0].album.prettify()} to {magenta('Library')}!")
                else:
                    print(f"Something went wrong while adding to {magenta('Library')} (status code: {saved.status_code})")

        if args.lastfm:
            artist_fmt = lambda t: t.get("artist").replace(" ", "+").split(",")[0]
            track_artists = set(artist_fmt(t) for t in tracks)
            track_albums = set((
                artist_fmt(t), 
                (t.get("album", "") if isinstance(t.get("album", ""), str) else t.get("album", {}).get("name", "")).replace(" ", "+")
            ) for t in tracks)
            track_songs = set((artist_fmt(t), t.get("name", "").replace(" ", "+")) for t in tracks)
            
            if args.song:
                for art, s in track_songs:
                    webbrowser.open(f"https://www.last.fm/user/{args.lastfm}/library/music/{art}/_/{s}")
            elif mode == 'albums':
                for art, alb in track_albums:
                    webbrowser.open(f"https://www.last.fm/user/{args.lastfm}/library/music/{art}/{alb}")
            else:
                for t in track_artists:
                    webbrowser.open(f"https://www.last.fm/user/{args.lastfm}/library/music/{t}")
        elif args.lastfm is not None:
            print("Could not find a valid last.fm user!")
        
        if args.spotify:
            if tracks:
                webbrowser.open(f"spotify://{tracks[-1].get('uri')}")
            else:
                print("Could not get context to open!")

if __name__ == '__main__':
    try:
        queue_track()
    except KeyboardInterrupt:
        exit(0)
