import json
import os
import pytz

from datetime import datetime, timedelta, tzinfo

import requests
import pylast

from utilities import search, get_token

spotify = get_token()
lastfm_file = os.path.join(os.path.dirname(__file__), "credentials", "lastfm.json")

with open(lastfm_file, "r") as cf:
    lastfm_creds = json.load(cf)

lastfm = pylast.LastFMNetwork(
    api_key=lastfm_creds["api_key"],
    api_secret=lastfm_creds["api_secret"],
    username=lastfm_creds["username"],
)

def get_top_tracks(start_date, end_date, limit=25):
    ts = lambda dt: int(dt.timestamp())
    resp = requests.get(
        "http://ws.audioscrobbler.com/2.0/?",
        params={
            "method": "user.getweeklytrackchart",
            "user": "Nathansbud",
            "from": ts(start_date),
            "to": ts(end_date),
            "limit": limit,
            "api_key": lastfm_creds["api_key"],
            "format": "json"
        }
    ).json()

    return [{
        "artist": t["artist"]["#text"],
        "title": t["name"],
        "plays": t["playcount"]  
    } for t in resp["weeklytrackchart"]["track"]]

# annoying limitation: Spotify API doesn't really expose playlist folders through the API, so can't set
def make_date_playlist(name, start_date, end_date, limit=25, description="", public=True):
    top_tracks = [
        search(t["title"], t["artist"], spotify)
        for t in get_top_tracks(start_date, end_date, limit)
    ]
    
    created_playlist = spotify.post(
        "https://api.spotify.com/v1/users/6rcq1j21davq3yhbk1t0l5xnt/playlists",
        data=json.dumps({
            "name": name,
            "public": public,
            **({} if not description else {"description": description})
        })
    ).json()

    spotify.post(f"https://api.spotify.com/v1/playlists/{created_playlist.get('id')}/tracks?uris={','.join((turi for turi in top_tracks if turi))}")

if __name__ == "__main__":
    TZ = pytz.timezone("US/Eastern")
    
    month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    for i in range(1, 10):
        make_date_playlist(
            f"{month[i - 1]} 2022",
            datetime(2022, i, 1, 0, 0, 1, tzinfo=TZ),
            datetime(2022, i + 1, 1, 0, 0, 0, tzinfo=TZ),
            description=f"Most played tracks for {month[i - 1]} 2022 (per last.fm)"
        )    
