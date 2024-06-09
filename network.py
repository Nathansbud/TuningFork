from datetime import datetime
import os
import json
import ssl
import urllib
import webbrowser

from http.server import HTTPServer, SimpleHTTPRequestHandler
from math import inf
from time import sleep

from requests_oauthlib import OAuth2Session

from model import (
    TrackObject, AlbumObject,
    create_track_object, 
    create_album_object,
    create_active_track_object
)
from utilities import iso_or_datetime, red, magenta



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
class SpotifyClient(OAuth2Session):
    def __init__(self): 
        self.client = get_token()

    def get(self, *args, **kwargs): return self.client.get(*args, **kwargs)
    def post(self, *args, **kwargs): return self.client.post(*args, **kwargs)
    def put(self, *args, **kwargs): return self.client.put(*args, **kwargs)
    
    def search(self, title, artist=None, mode='track') -> TrackObject | AlbumObject:
        if title and artist:
            resp = self.client.get(f"https://api.spotify.com/v1/search/?q={title.strip()}%20artist:{artist.strip()}&type={mode}&limit=1&offset=0").json()
        elif title:
            resp = self.client.get(f"https://api.spotify.com/v1/search/?q={title.strip()}&type={mode}&limit=1&offset=0").json()

        if mode == 'track':
            result = resp.get('tracks', {}).get('items')        
            return create_track_object(result[0])
        else:
            result = resp.get('albums', {}).get('items')
            return create_album_object(result[0])
        
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
                items.append(create_track_object(t))

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
    
    def get_current_track(self):
        response = self.client.get("https://api.spotify.com/v1/me/player/currently-playing")
        if response.status_code == 204:
            return None
            
        return create_active_track_object(response.json())
    
    def get_queue(self):
        response = self.client.get("https://api.spotify.com/v1/me/player/queue").json()
        current = response['currently_playing']
        if current: 
            return [
                create_track_object(response['currently_playing'])
            ] + [create_track_object(t) for t in response['queue']]

        return []

    def skip(self, times=1):
        for _ in range(times): 
            resp = self.client.post("https://api.spotify.com/v1/me/player/next")
            if resp.status_code == 404:
                return 404
        return 200

    def playpause(self, pause=True):
        base_url = "https://api.spotify.com/v1/me/player"
        player = self.client.get(base_url)
        if not 200 <= player.status_code < 300 or player.status_code == 204:
            return False, False
    
        if player.json().get("is_playing"):
            self.client.put(f"{base_url}/pause")
            return True, True
        elif not pause:
            self.client.put(f"{base_url}/play")
            return True, False

        return True, pause

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            vol = self.client.put(f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume}", data=json.dumps({
                "volume_percent": volume
            }))

            return "VOLUME_CONTROL_DISALLOW" not in vol.text
        
        raise ValueError("Invalid volume level")
    """
       
    elif args.volume is not None:
        if 0 <= args.volume <= 100:
            vol = spotify.put(f"https://api.spotify.com/v1/me/player/volume?volume_percent={args.volume}", data=json.dumps({
                "volume_percent": args.volume
            }))

            if "VOLUME_CONTROL_DISALLOW" in vol.text:
                print(f"Unfortunately, the current device {red('does not allow')} programmatic volume changes!")
            else:
                print(f"Set device volume to {green(args.volume)}%!")
        else:
            print(f"{magenta('Volume level')} must be a value from {bold('0–100')}!")
        
        exit(0)
        """

client = SpotifyClient()

if __name__ == '__main__':
    print(client.get_queue())