import argparse
import itertools
import json
import os
import re
import ssl
import urllib
import webbrowser

from datetime import datetime
from enum import Enum
from http.server import HTTPServer, SimpleHTTPRequestHandler
from math import inf
from subprocess import Popen, PIPE
from time import sleep
from typing import Union

from requests_oauthlib import OAuth2Session
from simple_term_menu import TerminalMenu

ESC = "\033"
DEFAULT = "\033[0m"
class Colors(Enum):
    BLACK = "0"
    RED = "1"
    GREEN = "2"
    YELLOW = "3"
    BLUE = "4"
    MAGENTA = "5"
    CYAN = "6"
    WHITE = "7"

def rgb(text: str, rgb_triple: tuple) -> str:
    return f"\033[38;2;{rgb_triple[0]};{rgb_triple[1]};{rgb_triple[2]}m{text}{DEFAULT}"

def cc(text: str, color_code: int) -> str:
    return f"\033[38;5;{color_code}m{text}{DEFAULT}"

def color(text, foreground=None, background=None):
    return f"\033[{('3' + foreground.value + ';') if foreground else ''}{('4' + background.value + ';') if background else ''}1m{text}{DEFAULT}"

def col(text, c, background):
    if not background: return color(text, c)
    else: return color(text, None, c)

def black(text, bg=False): return col(text, Colors.BLACK, bg)
def red(text, bg=False): return col(text, Colors.RED, bg)
def green(text, bg=False): return col(text, Colors.GREEN, bg)
def yellow(text, bg=False): return col(text, Colors.YELLOW, bg)
def blue(text, bg=False): return col(text, Colors.BLUE, bg)
def magenta(text, bg=False): return col(text, Colors.MAGENTA, bg)
def cyan(text, bg=False): return col(text, Colors.CYAN, bg)
def white(text, bg=False): return col(text, Colors.WHITE, bg)
def bold(text): return color(text)
def rainbow(text, bg=False): 
    return "".join([
        f"{col(l, c if not bg else None, c if bg else None)}" 
        for l, c in zip(text, itertools.cycle(list(Colors)[1:-1]))
    ])


cred_path = os.path.join(os.path.dirname(__file__), "credentials")
auth_url, token_url = "https://accounts.spotify.com/authorize", "https://accounts.spotify.com/api/token"        
default_spotify_scopes = [
    "playlist-modify-private", 
    "playlist-modify-public", 
    "ugc-image-upload",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-library-modify",
    "user-library-read"
]

with open(os.path.join(cred_path, "spotify.json"), "r") as jf: 
    try:
        spotify_creds = json.load(jf)
    except json.JSONDecodeError: 
        spotify_creds = {}

def start_server(port):    
    #Certificate files can be generated using: 
    #openssl req -x509 -sha256 -nodes -newkey rsa:2048 -days 365 -keyout localhost.key -out localhost.crt

    httpd = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket, 
        certfile=os.path.join(os.path.dirname(__file__), "certificates", "nathansbud.crt"), 
        keyfile=os.path.join(os.path.dirname(__file__), "certificates", "nathansbud.key"), server_side=True
    )
    httpd.serve_forever()

def authorize_spotify(scope):
    spotify = OAuth2Session(spotify_creds['client_id'], scope=scope, redirect_uri=spotify_creds['redirect_uri'])
    authorization_url, state = spotify.authorization_url(auth_url, access_type="offline")
    
    print("Opening authorization URL...paste redirect URL: ", end='')
    sleep(0.5)
    webbrowser.open_new(authorization_url)
    
    redirect_response = input()
    code = urllib.parse.parse_qs(
        urllib.parse.urlsplit(redirect_response, scheme='', allow_fragments=True).query
    ).get('code', [None])[0]
    token = spotify.fetch_token(token_url, client_secret=spotify_creds['client_secret'], code=code)

    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)
    return spotify

def save_token(token):
    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)

def get_token():
    CLIENT = None

    if not os.path.isfile(os.path.join(cred_path, "spotify_token.json")):
        CLIENT = authorize_spotify(default_spotify_scopes)
    else:
        with open(os.path.join(cred_path, "spotify_token.json"), 'r+') as t:
            token = json.load(t)
        
        CLIENT = OAuth2Session(spotify_creds['client_id'], token=token,
                                auto_refresh_url=token_url,
                                auto_refresh_kwargs={'client_id': spotify_creds['client_id'], 'client_secret': spotify_creds['client_secret']},
                                token_updater=save_token)    
    return CLIENT

def get_cookies():
    if spotify_creds.get("cookies"):
        expiry_date = datetime.fromisoformat(spotify_creds["cookies"]["expiration"][:-1])
        if datetime.now() > expiry_date:
            print(f'{red("Internal cookies have expired")}, make sure to update before attempting to use internal APIs!')
        else:
            return spotify_creds['cookies']['entries']
            
    return {}
        
def call_applescript(script):
    p = Popen(['osascript'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    return {"output": stdout, "error": stderr, "code": p.returncode}

def get_share_link(track, apple=False):
    # this depends on the shortcut used here https://www.icloud.com/shortcuts/54fcecba0c614f97ab2d664b6ea21450,
    # which uses the iTunes Search API to get back an Apple Music track; not guaranteed to continue working on 
    # future macOS versions (and will not work for Windows)
    
    # copy the passed in track URI to a URL
    process = Popen(['pbcopy'], env={'LANG': 'en_US.UTF-8'}, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    _, procerr = process.communicate(bytes(track.encode('UTF-8')))

    if apple:
        p = Popen(['shortcuts', 'run', 'spotify-to-apple-music-link'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return {"link": stdout, "error": stderr,"code": p.returncode}

    return {"link": track, "error": procerr, "code": process.returncode}

def get_vocal_paths():
    get_tracks = """
    tell application "iTunes"
        set vocalPaths to (get location of (every track in library playlist 1 whose (comment is "Vocal")))
        repeat with i from 1 to (count vocalPaths)
            set item i of vocalPaths to (POSIX path of item i of vocalPaths)
        end repeat
        set vocalPOSIX to vocalPaths
    end tell
    """
    return [f"/{s.lstrip('/')}".strip() for s in call_applescript(get_tracks)['output'].split(", /")]

def get_current_track():
    split_on =  "--------"
    get_current = f"""
		if application "Spotify" is running then
			tell application "Spotify"
                set theTrack to current track
                copy (name of theTrack as text) & "{split_on}" & (artist of theTrack as text) & "{split_on}" & (album of theTrack as text) to stdout
			end tell            
		end if
    """    
    
    current_track = call_applescript(get_current).get('output').strip().split(split_on)
    return {"title": current_track[0], "artist": current_track[1], "album": current_track[2]} if len(current_track) == 3 else None

def send_message_to_user(contact, msg):
    send_to_user = f"""
        tell application "Messages"
	        set targetService to 1st account whose service type = iMessage
	        set targetCell to participant "{contact}" of targetService
	        send "{msg}" to targetCell
        end tell
    """

    return call_applescript(send_to_user)

def remove_after(inp, endings=None, regex_endings=None):
    if regex_endings:
        for r in regex_endings: 
            inp = re.split(r, inp)[0]

    if endings:
        for ending in endings:
            if ending in inp: inp = inp.split(ending)[0].strip()

    return inp

def remove_remaster(inp):
    return remove_after(
        inp, 
        endings=[
            ' (Expanded', 
            ' (Deluxe', 
            ' (Original Mono', 
            ' (Remastered', 
            ' (Bonus', 
            ' (Legacy Edition', 
            ' (Super Deluxe Edition',
            ' (Special Edition',
            ' ['
        ], 
        regex_endings=[
            r'\s\(\d{4} Remaster',
            r'Remastered\s\d{4}',
            r'\(\d+(.*?) Anniversary(.*?)Edition'
        ]
    )

def dropdown(options: dict):
    # options contains k-v pairs
    o_keys = list(options.keys())
    select = TerminalMenu(o_keys)
    selected = select.show()
    if selected is not None: 
        return o_keys[selected], selected
    
    return None, None

def album_format(alb: dict, use_color=True):
    alb_o = alb.get('album', alb)
    
    if not isinstance(alb_o, str):
        alb_name = alb_o.get('name')
        alb_artist = ', '.join(artist.get('name') for artist in alb_o.get('artists', []))
    else:
        alb_name = alb.get('album')
        alb_artist = alb.get('artist')

    if use_color:
        return f"{color(alb_name, Colors.CYAN)} by {color(alb_artist, Colors.YELLOW)}"
    else:
        return f"{alb_name} by {alb_artist}"

def track_format(track: dict, use_color=True, album=False): 
    track_name = track.get('name')
    track_artist = ', '.join([artist.get('name') for artist in track.get('artists', [])]) if not track.get('artist') else track.get('artist')
    alb_name = track.get('album', {}).get('name') if type(track.get('album')) != str else track.get('album')

    if use_color:
        if not album or not alb_name:
            return f"{color(track_name, Colors.GREEN)} by {color(track_artist, Colors.YELLOW)}" 
        elif alb_name:
            return f"{color(track_name, Colors.GREEN)} by {color(track_artist, Colors.YELLOW)} ({cyan(alb_name)})" 
    else:
        if not album or not alb_name:
            return f"{track_name} by {track_artist}"
        elif alb_name:
            return f"{track_name} by {track_artist} ({alb_name})"


class SongException(Exception): pass
class SongParser(argparse.ArgumentParser):
    def error(self, msg):
        raise SongException("Invalid track specifier!")

def timestamp(ms): 
    secs, mils = divmod(ms, 1000)
    mins, secs = divmod(secs, 60)
    return (f'{int(mins)}:{int(secs):02d}')

def time_progress(curr, total, paren=False):
    return ('(' * paren) + f"{bold(timestamp(curr))} / {bold(timestamp(total))}" + (')' * paren)

def iso_or_datetime(iso_or_datetime: Union[str, datetime]):
    if isinstance(iso_or_datetime, str): 
        return datetime.fromisoformat(iso_or_datetime)
    elif isinstance(iso_or_datetime, datetime):
        return iso_or_datetime
    
    return None

class SpotifyClient(OAuth2Session):
    def __init__(self): 
        self.client = get_token()

    def get(self, *args, **kwargs): return self.client.get(*args, **kwargs)
    def post(self, *args, **kwargs): return self.client.post(*args, **kwargs)
    def put(self, *args, **kwargs): return self.client.put(*args, **kwargs)
    
    def search(self, title, artist=None, mode='track'):
        if title and artist:
            resp = self.client.get(f"https://api.spotify.com/v1/search/?q={title.strip()}%20artist:{artist.strip()}&type={mode}&limit=1&offset=0").json()
        elif title:
            resp = self.client.get(f"https://api.spotify.com/v1/search/?q={title.strip()}&type={mode}&limit=1&offset=0").json()
        
        return (resp.get('tracks', {}).get('items') or [{}])[0].get('uri')

    def get_library_albums(self, earliest=None, latest=None, limit=inf):
        lb = iso_or_datetime(earliest) or datetime.min
        ub = iso_or_datetime(latest) or datetime.max

        library = []
        request_url = "https://api.spotify.com/v1/me/albums?limit=50&offset=0"
        
        should = True
        seen = 0
        while should:
            resp = self.client.get(request_url).json()
            albums = resp['items']
            
            for a in albums:
                # drop trailing Z, which isn't valid ISO format
                added = datetime.fromisoformat(a['added_at'][:-1])
                
                # this is deeply upsetting to me (as it makes this method incredibly slow), 
                # but Spotify's Library API uses Recent sort (not Recently Added sort), with no option
                # to specify sort option, meaning older albums that are played gate any "new" albums before 
                # them from being added; this does not affect library tracks (which is just a playlist), which 
                # can use the much more performant early-exit approach:
                #
                #   if added <= lb:
                #       should = False
                #       break
                #   elif added > ub:
                #       continue
                #
                # will investigate when looking @ internal API, since there ought to be a better way...
                
                if ub >= added >= lb:
                    library.append((a['album'], added))
                
                seen += 1
            
            if seen >= limit: 
                should = False
            else:
                request_url = resp.get('next')
                if not request_url:
                    should = False
        
        # return in sorted order based on date
        return sorted(library, key=lambda v: v[1])[::-1] 

    def get_library_album_tracks(self, earliest=None, latest=None, limit=inf):
        albums = self.get_library_albums(earliest, latest, limit)
        items = [album[0]['tracks']['items'] for album in albums]
        return [t['uri'] for tracks in items for t in tracks]    
        
    def get_library_tracks(self, earliest=None, latest=None):
        return [t[0] for t in self.get_playlist_tracks(earliest, latest, playlist_id=None)]

    def get_playlist_tracks(
        self,
        earliest=None, 
        latest=None,
        playlist_id=None, 
        limit=inf
    ):
        lb = iso_or_datetime(earliest) or datetime.min
        ub = iso_or_datetime(latest) or datetime.max
        
        additions = []
        
        request_url = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0" if not playlist_id else f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=50&offset=0"
        
        should = True
        while should:
            resp = self.client.get(request_url).json()        
            tracks = resp['items'] if 'items' in resp else resp['tracks']['items']
            for t in tracks:
                # drop trailing Z, which isn't valid ISO format
                added = datetime.fromisoformat(t['added_at'][:-1])
                if added <= lb or len(additions) >= limit:
                    should = False
                    break
                elif added > ub:
                    continue
                
                additions.append((t['track']['uri'], t))
            
            request_url = resp.get('next')
            if not request_url:
                should = False

        return additions

    def get_album_tracks(self, album_id):
        request_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        items = []

        should = True
        while should:
            resp = self.client.get(request_url).json()        
            tracks = resp['items']
            for t in tracks:
                items.append(t)

            request_url = resp.get('next')
            if not request_url:
                should = False
        
        return items

    def remove_playlist_tracks(self, playlist_id, track_uris):
        if len(track_uris) > 100: 
            # TODO: Do this right
            raise ValueError("Can only remove max 100 tracks at a time (Zack was lazy)")
        
        request_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        self.client.delete(
            request_url,
            data=json.dumps({"tracks": [{"uri": t} for t in track_uris]})
        )

if __name__ == '__main__':
    client = SpotifyClient()
    pass
