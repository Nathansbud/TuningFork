import os
import json
import time
from math import ceil

import re

from parser import get_tracks
from unidecode import unidecode


feat_split = [" ft\. ", " feat\. ", " featuring\. ", " \(with "]

playlists = {
    "all":"2bQJC2lUa4pXkAt2qQejlx",
    "Vibe Check":"7vCyHDvq0dBwbfsyZMwUIn",
    "Feel the Wooz":"3O2xBhsDTbYDCvrU4YAUcM",
    "Jackin' It":"3O2xBhsDTbYDCvrU4YAUcM",
    "New Directions":"392ZrJDVDuiCIaDQYNBqVw"
}

def spotify_clean(field):
    unicode_cleaned = unidecode(field)
    feat_cleaned = re.split("\sfeat\.\s|\sft\.\s|\sfeaturing\s", unicode_cleaned)[0]
    field_cleaned = re.sub(r"[^a-zA-Z0-9]", " ", feat_cleaned).strip()
    space_cleaned = re.sub(r"\s+", "+", field_cleaned)
    return space_cleaned.lower()

def migrate_library(pid=playlists['all'], from_playlist=None, clear=False, tracks=[]):
    spotify = get_token()

    if clear:
        spotify.put(f"https://api.spotify.com/v1/playlists/{pid}/tracks",
                    data=json.dumps({'uris':[]}),
                    headers={"Content-Type": "application/json"})


    playlist_uris = set()
    total_items = 100 #minimum tracks returned is 100
    has_updated = False
    i = 0
    while i < ceil(total_items / 100):
        playlist = spotify.get(f"https://api.spotify.com/v1/playlists/{pid}/tracks/?fields=total,items(track(uri))&offset={100*i}").json()
        if not has_updated:
            total_items = playlist['total']
            has_updated = True

        for it in [item['track']['uri'] for item in playlist['items']]:
            playlist_uris.add(it)

        i += 1
    track_uris = set()
    failed = set()
    add_tracks = lambda ts: spotify.post(f"https://api.spotify.com/v1/playlists/{pid}/tracks", data=json.dumps({"uris":list(ts)}), headers={"Content-Type": "application/json"})
    for track in (get_tracks(from_playlist)[::-1] if from_playlist else tracks): #Reverse to get newest first
        oname = track['Name'] if not tracks else track[0]
        oartist = track['Artist'] if not tracks else track[1]

        name = spotify_clean(oname)
        artist = spotify_clean(oartist)
        st = spotify.get(f"https://api.spotify.com/v1/search/?q={name}%20artist:{artist}&type=track&limit=1&offset=0").json()
        track_uri = st['tracks']['items'][0]['uri'] if st['tracks']['items'] else ""
        if track_uri and not track_uri in playlist_uris:
            track_uris.add(track_uri)
        elif not track_uri:
            print(f"Failed to add {oname} by {oartist}")
            failed.add(f"{oname} by {oartist}")

        if len(track_uris) >= 100:
            add_tracks(track_uris)
            track_uris = set()

    if len(track_uris) > 0: add_tracks(track_uris)
    with open(os.path.join(os.path.dirname(__file__), "data", "failed.txt"), "w+") as ff:
        ff.writelines(map(lambda l: l+"\n", list(failed)))

if __name__ == '__main__':
    pass
