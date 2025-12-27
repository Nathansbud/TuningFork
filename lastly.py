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

from network import client as spotify
from preferences import prefs
from utilities import magenta

MODE = "auto"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

lastfm_file = os.path.join(os.path.dirname(__file__), "credentials", "lastfm.json")
atom_dir = os.path.join(os.path.dirname(__file__), "resources", "atoms")

with open(lastfm_file, "r") as cf: lastfm_creds = json.load(cf)

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

    if 'error' in resp:
        print(f"Received last.fm error while fetching tracks: {resp['message']}")
        return [] 
    
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
    if not prefs.get("SPOTIFY_USER"): 
        print(f"Could not find preference {magenta('SPOTIFY_USER')}, exiting...")
        return
    
    lastfm_chart = get_top_tracks(start_date, end_date, limit)
    raw_tracks = [
        spotify.search(t["name"], t["artist"])
        for t in get_top_tracks(start_date, end_date, limit)
    ]

    top_tracks = []
    for (raw, last) in zip(raw_tracks, lastfm_chart):
        if not raw: print(f"Failed to fetch track: {last} from last.fm!")
        else:
            top_tracks.append(raw)

    if not top_tracks: 
        print("Found no tracks in provided range; exiting...")
        return

    playlist_id = spotify.create_playlist(
        name,
        public=public,
        description=description
    )

    spotify.add_playlist_tracks(playlist_id, top_tracks)

    # for some reason, the playlist takes a bit before a playlist cover can be updated; wait a few seconds first
    if image:
        sleep(5)
        spotify.set_playlist_image(
            playlist_id, 
            build_playlist_image(start_date)
        )
        
    print(f"Created playlist {name}!")

def generate_last_month_playlist(dt):
    this_month = dt.replace(day=1, hour=0, minute=0, second=0)

    # Last.fm is upper-bound inclusive, weirdly; hence, we want to do between midnight
    # on the first day of the month to 11:59 on the final day of the month
    start_last_month = (this_month - timedelta(days=1)).replace(day=1)
    end_last_month = (this_month - timedelta(seconds=1))
    playlist_for = f"{MONTHS[start_last_month.month - 1]} {start_last_month.year}"
    make_date_playlist(
        playlist_for,
        start_last_month,
        end_last_month,
        description=f"most played tracks for {playlist_for} (per last.fm)"
    ) 
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser("Lastly")
    parser.add_argument("--mode", default="auto")
    args = parser.parse_args()

    TZ = pytz.timezone("US/Eastern")
    if args.mode == "auto":
        generate_last_month_playlist(datetime.now(tz=TZ))
    elif args.mode == "year":
        current_year = datetime.now(tz=TZ).year
        make_date_playlist(
            "YIZ25: Zpotify Wrapped",
            datetime.now(tz=TZ).replace(month=1, day=1, hour=0, minute=0, second=0),
            datetime.now(tz=TZ).replace(year=current_year + 1, month=1, day=1, hour=0, minute=0, second=0),
            description=f"my 100 (ish) most played songs of {current_year}, per last.fm",
            limit=100
        )
    else:
        pass