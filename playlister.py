import json
import os

from datetime import datetime

import requests

from utilities import get_token

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
    bound = datetime.fromisoformat(last_update) if last_update else datetime.min

    time_now = datetime.utcnow().isoformat()
    
    additions = []
    request_url = f"https://api.spotify.com/v1/me/albums?limit=50&offset=0"
    
    should = True
    while should:
        resp = spotify.get(request_url).json()
        albums = resp['items']

        for a in albums:
            # drop trailing Z, which isn't valid ISO format
            added = datetime.fromisoformat(a['added_at'][:-1])

            if added <= bound:
                should = False
                break
            
            track_uris = [t['uri'] for t in a['album']['tracks']['items']]
            additions.extend(track_uris)
    
        request_url = resp.get('next')
        if not request_url:
            should = False
        
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
    bound = datetime.fromisoformat(last_update) if last_update else datetime.min

    time_now = datetime.utcnow().isoformat()
    
    additions = []
    request_url = f"https://api.spotify.com/v1/me/tracks?limit=50&offset=0"
    
    should = True
    while should:
        resp = spotify.get(request_url).json()
        tracks = resp['items']
        for t in tracks:
            # drop trailing Z, which isn't valid ISO format
            added = datetime.fromisoformat(t['added_at'][:-1])
            if added <= bound:
                should = False
                break
            
            additions.append(t['track']['uri'])
        
        request_url = resp.get('next')
        if not request_url:
            should = False

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

if __name__ == "__main__":
    if internet():
        update_liked_playlist(
            cache["LIKED_METADATA"]["ACTIVE_PLAYLIST_URI"].split(":")[-1],
            cache["LIKED_METADATA"]["LAST_UPDATE"],
        )

        update_library_playlist(
            cache["LIBRARY_METADATA"]["ACTIVE_PLAYLIST_URI"].split(":")[-1],
            cache["LIBRARY_METADATA"]["LAST_UPDATE"],
        )
