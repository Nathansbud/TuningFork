import json
import os

from datetime import datetime

import requests

from utilities import (
    get_token, 
    get_library_album_tracks, get_library_tracks, get_playlist_tracks, get_album_tracks
)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "resources", "playlister.json")

spotify = get_token()

def internet():
    connection = True
    try:
        r = requests.get("https://google.com")
        r.raise_for_status()
    except:
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

def update_library_playlist(playlist_id, last_update=None):
    time_now = datetime.utcnow().isoformat()
    additions = get_library_album_tracks(last_update, client=spotify)

    BATCH_SIZE = 100
    batched = [
        additions[i:i+BATCH_SIZE] for i in range(0, len(additions), BATCH_SIZE)
    ][::-1]

    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
        )

    cache["LIBRARY_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

def update_liked_playlist(playlist_id, last_update=None):
    time_now = datetime.utcnow().isoformat()
    additions = get_library_tracks(last_update, client=spotify)

    BATCH_SIZE = 100
    batched = [
        additions[i:i+BATCH_SIZE] for i in range(0, len(additions), BATCH_SIZE)
    ][::-1]
    
    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
        )

    cache["LIKED_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

def update_backlog_playlist(playlist_id, backlog_id, last_update=None):
    time_now = datetime.utcnow().isoformat()
    backlog = get_playlist_tracks(last_update, playlist_id=backlog_id, client=spotify)
    
    additions = []
    for b in backlog:
        additions.extend([t['uri'] for t in get_album_tracks(b[1]['track']['album']['id'], spotify)])
    
    BATCH_SIZE = 100
    batched = [
        additions[i:i+BATCH_SIZE] for i in range(0, len(additions), BATCH_SIZE)
    ][::-1]
    
    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
        )

    cache["BACKLOG_METADATA"]["LAST_UPDATE"] = time_now
    save_cache()

if __name__ == "__main__":
    if internet():
        update_liked_playlist(
            cache["LIKED_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["LIKED_METADATA"]["LAST_UPDATE"],
        )
        
        update_library_playlist(
            cache["LIBRARY_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["LIBRARY_METADATA"]["LAST_UPDATE"],
        )

        update_backlog_playlist(
            cache["BACKLOG_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["BACKLOG_METADATA"]["BACKLOG_PLAYLIST_ID"],
            cache["BACKLOG_METADATA"]["LAST_UPDATE"],
        )
