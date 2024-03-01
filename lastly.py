import argparse
import base64
import json
import os
import pytz

from datetime import datetime, timedelta
from io import BytesIO
from time import sleep

import requests
from PIL import Image

from utilities import search, get_token

MODE = "auto"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

spotify = get_token()
lastfm_file = os.path.join(os.path.dirname(__file__), "credentials", "lastfm.json")
prefs_file = os.path.join(os.path.dirname(__file__), "resources", "preferences.json")
atom_dir = os.path.join(os.path.dirname(__file__), "resources", "atoms")

with open(lastfm_file, "r") as cf: lastfm_creds = json.load(cf)
with open(prefs_file, "r") as pf: prefs = json.load(pf)

def get_current_track(user): 
    k = get_recent_tracks(user, 1)
    return k[0] if k else []

def get_recent_tracks(user, limit=25):
    resp = requests.get(
        "http://ws.audioscrobbler.com/2.0/?",
        params={
            "method": "user.getrecenttracks",
            "user": user,
            "limit": limit,
            "api_key": lastfm_creds["api_key"],
            "format": "json"
        }
    ).json()

    return [{
        "artist": t["artist"]["#text"],
        "name": t["name"],
    } for t in resp["recenttracks"]["track"]]
    

def get_top_tracks(start_date, end_date, limit=25, user=prefs.get("LASTFM_USER")):
    ts = lambda dt: int(dt.timestamp())
    resp = requests.get(
        "http://ws.audioscrobbler.com/2.0/?",
        params={
            "method": "user.getweeklytrackchart",
            "user": user,
            "from": ts(start_date),
            "to": ts(end_date),
            # "limit": limit,
            "api_key": lastfm_creds["api_key"],
            "format": "json"
        }
    ).json()
    
    unlimited = [{
        "artist": t["artist"]["#text"],
        "name": t["name"],
        "plays": t["playcount"]  
    } for t in resp["weeklytrackchart"]["track"]]
    
    last = limit
    if len(unlimited) > limit: 
        last_plays = unlimited[limit - 1]["plays"]
        for l in unlimited[limit:]:
            if l["plays"] == last_plays:
                last += 1
            else:
                break
    
    return unlimited[:last]


def build_playlist_image(dt: datetime):
    with \
        Image.open(os.path.join(atom_dir, f"{dt.month:02d}.png")) as month_atom, \
        Image.open(os.path.join(atom_dir, f"{dt.year}.png")) as year_atom, \
        Image.open(os.path.join(atom_dir, f"blackground.png")) as bg:
        bg.alpha_composite(month_atom)
        bg.alpha_composite(year_atom)
        
        buff = BytesIO()
        bg.convert('RGB').save(buff, format='JPEG', quality=100, subsampling=0)
        return base64.b64encode(buff.getvalue())

# annoying limitation: Spotify API doesn't really expose playlist folders through the API, so can't set
def make_date_playlist(name, start_date, end_date, limit=25, description="", public=True, image=True):
    top_tracks = [
        search(t["name"], t["artist"], spotify)
        for t in get_top_tracks(start_date, end_date, limit)
    ]

    print(f"Building playlist {name}...")
    created_playlist = spotify.post(
        f"https://api.spotify.com/v1/users/{prefs.get('SPOTIFY_USER')}/playlists",
        data=json.dumps({
            "name": name,
            "public": public,
            **({} if not description else {"description": description})
        })
    ).json()

    BATCH_SIZE = 100
    batched = [
        top_tracks[i:i+BATCH_SIZE] for i in range(0, len(top_tracks), BATCH_SIZE)
    ][::-1]

    for b in batched:
        spotify.post(
            f"https://api.spotify.com/v1/playlists/{created_playlist.get('id')}/tracks",
            data=json.dumps({"uris": b, "position": 0})
        )

    # for some reason, the playlist takes a bit before a playlist cover can be updated; wait a few seconds first
    if image:
        sleep(5)
        playlist_image = build_playlist_image(start_date)
        img = spotify.put(
            f"https://api.spotify.com/v1/playlists/{created_playlist.get('id')}/images", 
            headers={'Content-Type': 'image/jpeg'},
            data=playlist_image
        )
    
    print(f"Created playlist {name}!")

def generate_last_month_playlist(dt):
    this_month = dt.replace(day=1, hour=0, minute=0, second=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1, second=0)
    playlist_for = f"{MONTHS[last_month.month - 1]} {last_month.year}"
    make_date_playlist(
        playlist_for,
        last_month,
        this_month,
        description=f"most played tracks for {playlist_for} (per last.fm)"
    ) 
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser("Lastly")
    parser.add_argument("--mode", default="auto")
    args = parser.parse_args()

    TZ = pytz.timezone("US/Eastern")
    if args.mode == "auto":
        generate_last_month_playlist(datetime.now(tz=TZ))
