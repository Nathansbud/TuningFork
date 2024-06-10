import json
import os

from datetime import datetime

import requests

from network import client as spotify
from utilities import flatten

CACHE_FILE = os.path.join(os.path.dirname(__file__), "resources", "playlister.json")
DUMMY_PLAYLIST = "1ijioHJWs8eEhrG7UQSISo"
UPDATE_BACKLOG = False

def internet():
    connection = True
    try:
        r = requests.get("https://google.com")
        r.raise_for_status()
    except Exception:
        connection = False
    finally:
        return connection

def load_cache():
    if not os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, 'w+') as cf: 
            json.dump({
                "LIBRARY_METADATA": {
                    "LAST_UPDATE": datetime.min.isoformat(),
                    "ACTIVE_PLAYLIST": ""
                },
                "LIKED_METADATA": {
                    "LAST_UPDATE": datetime.min.isoformat(),
                    "ACTIVE_PLAYLIST": ""
                },
            }, cf, indent=2)
    
    with open(CACHE_FILE, "r+") as cf:
        return json.load(cf)
    
        
cache = load_cache()

def save_cache():
    with open(CACHE_FILE, "w+") as cf:
        json.dump(cache, cf, indent=2)

def update_library_playlist(playlist_id, last_update=None, limit=50):
    time_now = datetime.utcnow().isoformat()
    
    # in the interest of performance, only do last 50 played albums when updating; 
    # realistically, we won't have gotten backlogged past that point
    albums = spotify.get_library_albums(last_update, limit=limit)
    tracks = flatten([album.tracks for album in albums])
    spotify.add_playlist_tracks(playlist_id, tracks)

    cache["LIBRARY_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

def update_liked_playlist(playlist_id, last_update=None):
    time_now = datetime.utcnow().isoformat()
    spotify.add_playlist_tracks(
        playlist_id,
        spotify.get_library_tracks(last_update)
    )

    cache["LIKED_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

def update_backlog_playlist(playlist_id, backlog_id, last_update=None):
    time_now = datetime.utcnow().isoformat()
    
    backlog = spotify.get_playlist_tracks(last_update, playlist_id=backlog_id)
    tracks = flatten([
        spotify.get_album_tracks(album_id=track.album.id) 
        for track in backlog
    ])

    spotify.add_playlist_tracks(playlist_id, tracks)
    cache["BACKLOG_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

def sort_backlog_by_album_length(playlist_id, backlog_id):
    backlog = spotify.get_playlist_tracks(playlist_id=backlog_id)
    ordered = sorted([
        (item, spotify.get_album(album_id=item.album.id).duration) 
        for item in backlog
    ], key=lambda v: v[1])

    spotify.add_playlist_tracks(
        playlist_id,
        [pair[0] for pair in ordered]
    )
    
if __name__ == "__main__":
    if internet():
        # Would prefer to disable liked playlist -> Zacksongs, since workflow doesn't really make sense since 
        # considering the removal of the like button from UI, but programmatically can add new tracks to top of
        # playlist which is much preferred
        update_liked_playlist(
            cache["LIKED_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["LIKED_METADATA"]["LAST_UPDATE"],
        )
        
        update_library_playlist(
            cache["LIBRARY_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["LIBRARY_METADATA"]["LAST_UPDATE"],
        )
        
        if UPDATE_BACKLOG:
            update_backlog_playlist(
                cache["BACKLOG_METADATA"]["ACTIVE_PLAYLIST_ID"],
                cache["BACKLOG_METADATA"]["BACKLOG_PLAYLIST_ID"],
                cache["BACKLOG_METADATA"]["LAST_UPDATE"],
            )