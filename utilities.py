from subprocess import Popen, PIPE

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import json
import webbrowser
import urllib
from time import sleep 
import argparse
from enum import Enum

from requests_oauthlib import OAuth2, OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

class Colors(Enum):
    DEFAULT = "\033[0m"
    RED = "\033[31;1m"
    GREEN = "\033[32;1m"
    YELLOW = "\33[33;1m"
    BLUE = '\033[34;1m'
    MAGENTA = "\033[35;1m"
    CYAN = "\033[36;1m"
    WHITE = "\033[37;1m"

def color(text, color): return f"{color.value}{text}{Colors.DEFAULT.value}"

cred_path = os.path.join(os.path.dirname(__file__), "credentials")
default_spotify_scopes = [
    "playlist-modify-private", 
    "playlist-modify-public", 
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
    auth_url, token_url = "https://accounts.spotify.com/authorize", "https://accounts.spotify.com/api/token"

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
                                auto_refresh_url=spotify_creds['token_url'],
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

class SongException(Exception): pass
class SongParser(argparse.ArgumentParser):
    def error(self, msg):
        raise SongException("Invalid track specifier!")

if __name__ == '__main__':
    start_server(6813)
    pass
