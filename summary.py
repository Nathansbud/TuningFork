import json
import random

from datetime import datetime
from typing import List, Optional
from utilities import flatten

from network import client as spotify

def save_album_history(
    year: int, 
    allpath: Optional[str]=None, 
    yearpath: Optional[str]=None, 
    library_playlist_id: Optional[str]=None,
    year_playlist_id: Optional[str]=None,
    release_all: bool=False
):
    albums = spotify.get_library_albums(datetime(year - 1, 12, 31, 0, 0, 0))[::-1]    
    def name_fmt(alb, release=False):
        released = f' ({alb.released})' if release else ''

        return f'{alb.added.strftime("%m-%d")} - {alb.name} by {alb.artist}{released}\n'
    
    if allpath:
        with open(allpath, "w+") as allf:
            for alb in albums:
                allf.write(name_fmt(alb, release=release_all))
    
    if yearpath:
        with open(yearpath, "w+") as yearf:
            for alb in [a for a in albums if a.released.startswith(f"{year}")]:
                yearf.write(name_fmt(alb, release=True))

    if library_playlist_id:
        spotify.add_playlist_tracks(
            library_playlist_id, 
            flatten([t.tracks for t in albums])
        )

    if year_playlist_id:
        spotify.add_playlist_tracks(
            year_playlist_id,
            [a.tracks[0] for a in albums if a.released.startswith(f"{year}")]
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


