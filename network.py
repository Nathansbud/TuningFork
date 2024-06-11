from datetime import datetime
import os
import json
import ssl
from typing import List, Optional, Tuple
import urllib
import webbrowser

from http.server import HTTPServer, SimpleHTTPRequestHandler
from math import inf
from time import sleep

from requests_oauthlib import OAuth2Session

from utilities import iso_or_datetime, red
from model import (
    TrackObject, ActiveTrackObject, AlbumObject, SavedAlbumObject, PlaylistObject,
    create_saved_album_object,
    create_track_object, 
    create_album_object,
    create_active_track_object,
    create_playlist_object
)
from preferences import prefs




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
class SpotifyClient:
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
    
    def get_library_albums(self, earliest=None, latest=None, limit=inf) -> List[SavedAlbumObject]:
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
                if seen >= limit: break
                
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
                    library.append(create_saved_album_object(a))
                
                seen += 1
            
            if seen >= limit: 
                should = False
            else:
                request_url = resp.get('next')
                if not request_url:
                    should = False
        
        # return in sorted order based on date
        return sorted(library, key=lambda v: v.added)[::-1] 
        
    def get_library_tracks(self, earliest=None, latest=None, limit=inf):
        return self.get_playlist_tracks(
            earliest=earliest, 
            latest=latest,
            limit=inf,
            playlist_id=None
        )
    
    def get_playlist(self, playlist_id, include_tracks=False) -> Optional[PlaylistObject]:
        response = self.client.get(f"https://api.spotify.com/v1/playlists/{playlist_id}")
        if response.status_code != 200: 
            return None
        
        tracks = self.get_playlist_tracks(playlist_id=playlist_id) if include_tracks else None
        return create_playlist_object(response.json(), tracks)

    def get_playlist_tracks(
        self,
        earliest=None, 
        latest=None,
        playlist_id=None, 
        limit=inf
    ) -> List[TrackObject]:
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

                additions.append(create_track_object(t.get('track')))
            
            request_url = resp.get('next')
            if not request_url:
                should = False

        return additions

    def get_album(self, album_id) -> AlbumObject:
        response = self.client.get(f"https://api.spotify.com/v1/albums/{album_id}")
        return create_album_object(response.json())
        
    def get_album_tracks(self, *, album_id=None, album=None):
        if not (album_id or album): return []
        aid = album.id if album else album_id

        request_url = f"https://api.spotify.com/v1/albums/{aid}/tracks"
        items = []

        should = True
        while should:
            resp = self.client.get(request_url).json()      
            tracks = resp['items']
            for t in tracks:
                items.append(create_track_object(t, album=album))

            request_url = resp.get('next')
            if not request_url:
                should = False
        
        return items

    def create_playlist(self, name, public=True, description=""):
        if not prefs.get("SPOTIFY_USER"): return
        
        return self.client.post(
            f"https://api.spotify.com/v1/users/{prefs.get('SPOTIFY_USER')}/playlists",
            data=json.dumps({
                "name": name,
                "public": public,
                **({} if not description else {"description": description})
        })).json().get('id')

    def set_playlist_image(self, playlist_id: str, image: bytes):
        return self.client.put(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/images", 
            headers={'Content-Type': 'image/jpeg'},
            data=image
        )

    def add_playlist_tracks(self, playlist_id, tracks):
        flag_failure = False

        # Both track order AND batch order need to be reversed such that
        # the output has the expected ordering:
        # Input, Batched [X]:               
        #   ABC|DEF|GHI -> GHIDEFABC 
        # Reversed Input, Batched [X]:      
        #   IHG|FED|CBA -> CBAFEDIHG
        # Reversed Input, Reversed Batched: 
        #   IHG|FED|CBA -> ABCDEFGHI
        
        insert_order = tracks[::-1]
        BATCH_SIZE = 100
        for batch in [
            insert_order[i:i+BATCH_SIZE][::-1] for i in range(0, len(tracks), BATCH_SIZE)
        ]:
            response = self.client.post(
                f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                data=json.dumps({
                    "uris": [track.uri for track in batch], 
                    "position": 0
                })
            )
            
            flag_failure = flag_failure or response.status_code >= 300

        return not flag_failure

    def remove_playlist_tracks(self, playlist_id, tracks):
        flag_failure = False

        BATCH_SIZE = 100
        for batch in [
            tracks[i:i+BATCH_SIZE] for i in range(0, len(tracks), BATCH_SIZE)
        ]:
            response = self.client.delete(
                f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                data=json.dumps({
                    "tracks": [{"uri": track.uri} for track in batch]                
                })
            )
            
            flag_failure = flag_failure or response.status_code >= 300

        return not flag_failure

    def replace_all_playlist_tracks(self, playlist_id, tracks):
        # Clear existing tracks
        existing = self.get_playlist_tracks(playlist_id=playlist_id)
        self.remove_playlist_tracks(playlist_id, existing)
        
        self.add_playlist_tracks(playlist_id, tracks)
        
    def get_track(self, track_id: str) -> TrackObject | AlbumObject:
        response = self.client.get(f'https://api.spotify.com/v1/tracks/{track_id}')
        if response.status_code != 200: 
            return None
        
        return create_track_object(response.json())
    
    def get_current_track(self) -> ActiveTrackObject:
        response = self.client.get("https://api.spotify.com/v1/me/player/currently-playing")
        if response.status_code == 204:
            return None
            
        return create_active_track_object(response.json())
    
    def get_queue(self) -> List[TrackObject]:
        response = self.client.get("https://api.spotify.com/v1/me/player/queue").json()
        current = response['currently_playing']
        if current: 
            return [
                create_track_object(response['currently_playing'])
            ] + [create_track_object(t) for t in response['queue']]

        return []

    def get_recent_tracks(self, limit=1) -> List[TrackObject]:
        response = self.client.get(f"https://api.spotify.com/v1/me/player/recently-played?limit={limit}")
        if response.status_code != 200: 
            return []
        
        return [
            create_track_object(s.get('track')) 
            for s in response.json().get('items', [])
            if 'track' in s
        ][::-1]

    def skip(self, times: int=1) -> int:
        for _ in range(times): 
            resp = self.client.post("https://api.spotify.com/v1/me/player/next")
            if resp.status_code == 404:
                return 404
        return 200

    def playpause(self, pause=True) -> Tuple[bool]:
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

    def set_volume(self, volume: int):
        if 0 <= volume <= 100:
            vol = self.client.put(f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume}", data=json.dumps({
                "volume_percent": volume
            }))

            return "VOLUME_CONTROL_DISALLOW" not in vol.text
        
        raise ValueError("Invalid volume level")

    def queue(self, uri):
        response = self.client.post(f"https://api.spotify.com/v1/me/player/queue?uri={uri}")
        return response.status_code < 300

client = SpotifyClient()

if __name__ == '__main__':
    pass