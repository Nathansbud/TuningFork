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
    playlist_items = spotify.get_playlist_tracks(playlist_id=in_id)
    
    # unique-ify items by converting -> dict on item uri, then back
    unique_items = list({p.uri: p for p in playlist_items}.values())
    random.shuffle(unique_items)

    spotify.add_playlist_tracks(out_id, unique_items)

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

def merge_monthly_playlists(combined_id: str, year: int):
    valid_names = [
        f"{n} {year}" for n in 
        ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    ]

    spotify.merge_playlists(combined_id, lambda p: p.name in valid_names)

if __name__ == "__main__":
    pass


