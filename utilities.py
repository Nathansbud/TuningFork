from subprocess import Popen, PIPE

import os
import datetime
import itertools
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import json
import webbrowser
import urllib
from time import sleep 
import argparse
from enum import Enum
import re

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
        expiry_date = datetime.datetime.fromisoformat(spotify_creds["cookies"]["expiration"][:-1])
        if datetime.datetime.now() > expiry_date:
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

def search(title, artist=None, spotify=None, mode='track'):
    if not (spotify or title): return

    if title and artist:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}%20artist:{artist.strip()}&type={mode}&limit=1&offset=0").json()
    elif title:
        resp = spotify.get(f"https://api.spotify.com/v1/search/?q={title.strip()}&type={mode}&limit=1&offset=0").json()
    
    return (resp.get('tracks', {}).get('items') or [{}])[0].get('uri')

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

if __name__ == '__main__':
    start_server(6813)
    pass
