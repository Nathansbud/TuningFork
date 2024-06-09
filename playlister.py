import json
import os

from datetime import datetime

import requests

from network import client as spotify

CACHE_FILE = os.path.join(os.path.dirname(__file__), "resources", "playlister.json")
DUMMY_PLAYLIST = "1ijioHJWs8eEhrG7UQSISo"

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
    additions = spotify.get_library_album_tracks(last_update, limit=limit)

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
    additions = spotify.get_library_tracks(last_update)

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
    backlog = spotify.get_playlist_tracks(last_update, playlist_id=backlog_id)
    
    additions = []
    for b in backlog:
        additions.extend([t['uri'] for t in spotify.get_album_tracks(album_id=b[1]['track']['album']['id'])])
    
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

def sort_backlog_by_album_length(output_id, backlog_id):
    backlog = spotify.get_playlist_tracks(None, playlist_id=backlog_id)
    
    sorted_albums = sorted([
        (sum([t['duration_ms'] for t in spotify.get_album_tracks(album_id=b[1]['track']['album']['id'])]), b[0])
        for b in backlog
    ])

    album_ids = [a[1] for a in sorted_albums]

    BATCH_SIZE = 100
    batched = [
        album_ids[i:i+BATCH_SIZE] for i in range(0, len(album_ids), BATCH_SIZE)
    ][::-1]

    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{output_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
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

        update_backlog_playlist(
            cache["BACKLOG_METADATA"]["ACTIVE_PLAYLIST_ID"],
            cache["BACKLOG_METADATA"]["BACKLOG_PLAYLIST_ID"],
            cache["BACKLOG_METADATA"]["LAST_UPDATE"],
        )
