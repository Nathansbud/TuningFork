import json
import random
from datetime import datetime
from typing import List, Optional

from utilities import get_token, get_library_albums
from playlister import update_liked_playlist

spotify = get_token()

def save_album_history(
    year: int, 
    allpath: Optional[str]=None, 
    yearpath: Optional[str]=None, 
    library_playlist_id: Optional[str]=None, 
    release_all: bool=False
):
    albums = get_library_albums(datetime(year, 12, 21, 0, 0, 0), client=spotify)[::-1]
    
    def name_fmt(alb, added, release=False):
        alb_name = alb['name']
        alb_artist = " & ".join([art['name'] for art in alb['artists']])
        alb_added = added.strftime("%B %d").replace(" 0", " ")
        alb_release = f' ({alb["release_date"]})' if release else ''

        return f'{alb_added} - {alb_name} by {alb_artist}{alb_release}\n'
    
    if allpath:
        with open(allpath, "w+") as allf:
            for (alb, added) in albums:
                allf.write(name_fmt(alb, added, release=release_all))
    
    if yearpath:
        with open(yearpath, "w+") as yearf:
            for (alb, added) in [a for a in albums if a[0]['release_date'].startswith(f"{year}")]:
                yearf.write(name_fmt(alb, added, release=True))

    if library_playlist_id:
        items = [album[0]['tracks']['items'] for album in albums]
        tracks = [t['uri'] for tracks in items for t in tracks]
        
        BATCH_SIZE = 100
        batched = [
            tracks[i:i+BATCH_SIZE] for i in range(0, len(tracks), BATCH_SIZE)
        ][::-1]

        for b in batched:
            spotify.post(
                f"https://api.spotify.com/v1/playlists/{library_playlist_id}/tracks", 
                data=json.dumps({"uris": b, "position": 0})
            )

def create_shuffled(in_id: str, out_id: str):
    ts = set()
    
    for i in range(2):
        # heads up that the playlist endpoint doesn't support offset, only tracks does
        ts |= {
            t['track']['uri'] for t in spotify.get(
                f"https://api.spotify.com/v1/playlists/{in_id}/tracks?offset={i * 100}&limit=100"
            ).json()['items']
        }

    tracks = list(ts)
    random.shuffle(tracks)
    
    BATCH_SIZE = 100
    batched = [
        tracks[i:i+BATCH_SIZE] for i in range(0, len(tracks), BATCH_SIZE)
    ][::-1]

    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{out_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
        )

def combine_playlists(target_id: str, *pids: List[str]):
    tracks = []
    for p in pids:
        tracks.extend([
            t['track']['uri'] for t in spotify.get(
                f"https://api.spotify.com/v1/playlists/{p}/tracks?offset=0&limit=100"
            ).json()['items']
        ])
    
    BATCH_SIZE = 100
    batched = [
        tracks[i:i+BATCH_SIZE] for i in range(0, len(tracks), BATCH_SIZE)
    ][::-1]

    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{target_id}/tracks", 
            data=json.dumps({"uris": b, "position": 0})
        )

if __name__ == "__main__":
    pass


