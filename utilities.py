from subprocess import Popen, PIPE

import os
import itertools
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import json
import webbrowser
import urllib
from time import sleep 
import argparse
from enum import Enum

from requests_oauthlib import OAuth2Session
from simple_term_menu import TerminalMenu

class Colors(Enum):
    DEFAULT = "\033[0m"
    RED = "\033[31;1m"
    GREEN = "\033[32;1m"
    YELLOW = "\33[33;1m"
    BLUE = '\033[34;1m'
    MAGENTA = "\033[35;1m"
    CYAN = "\033[36;1m"
    WHITE = "\033[37;1m"

    # Does nothing on its own, but if passed to color used as a flag
    RAINBOW = ""


def color(text, color):
    if color != Colors.RAINBOW:
        return f"{color.value}{text}{Colors.DEFAULT.value}"
    else:
        return "".join([
            f"{c.value}{l}{Colors.DEFAULT.value}" 
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

def get_token(scope=default_spotify_scopes):
    if not os.path.isfile(os.path.join(cred_path, "spotify_token.json")):
        return authorize_spotify(default_spotify_scopes)
    else:
        with open(os.path.join(cred_path, "spotify_token.json"), 'r+') as t:
            token = json.load(t)
        return OAuth2Session(spotify_creds['client_id'], token=token,
                                auto_refresh_url=token_url,
                                auto_refresh_kwargs={'client_id': spotify_creds['client_id'], 'client_secret': spotify_creds['client_secret']},
                                token_updater=save_token)


def call_applescript(script):
    p = Popen(['osascript'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    return {"output": stdout, "error": stderr,"code": p.returncode}

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

def search(title, artist=None, spotify=None):
    if not (spotify or title): return

    if title and artist:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}%20artist:{artist.strip()}&type=track&limit=1&offset=0").json()
    elif title:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}&type=track&limit=1&offset=0").json()
    
    return (resp.get('tracks', {}).get('items') or [{}])[0].get('uri')

def dropdown(options: dict):
    # options contains k-v pairs
    o_keys = list(options.keys())
    select = TerminalMenu(o_keys)
    selected = select.show()
    if selected is not None: 
        return o_keys[selected], selected
    
    return None, None

def album_display(alb: dict, use_color=True):
    alb_o = alb.get('album', {})
    
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

def track_display(track: dict, use_color=True): 
    track_name = track.get('name')
    track_artist = ', '.join([artist.get('name') for artist in track.get('artists', [])])

    if use_color:
        return f"{color(track_name, Colors.GREEN)} by {color(track_artist, Colors.YELLOW)}"
    else:
        return f"{track_name} by {track_artist}"


class SongException(Exception): pass
class SongParser(argparse.ArgumentParser):
    def error(self, msg):
        raise SongException("Invalid track specifier!")

if __name__ == '__main__':
    start_server(6813)
    pass
