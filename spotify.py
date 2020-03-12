from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os
import json
from scraper import genius_clean, get_lyrics, make_genius_url
from profane import check_lyrics

with open(os.path.join(os.path.dirname(__file__), "credentials", "spotify.json")) as jf: creds = json.load(jf)
os.environ["SPOTIPY_CLIENT_ID"] = creds["client_id"]
os.environ["SPOTIPY_CLIENT_SECRET"] = creds["client_secret"]
sp = Spotify(client_credentials_manager=SpotifyClientCredentials())

def get_playlist(pid):
    playlist_tracks = sp.playlist(pid)['tracks']['items']
    tracks = {}
    for pt in playlist_tracks:
        track = pt['track']
        name = track['name'].lower()
        artists = [a['name'].lower() for a in track['artists']]
        if " (from " in name: name = name[:name.find("(from ")]
        if " recorded at " in name: name = name[:name.find(" recorded at ")]
        if " - live from " in name: name = name[:name.find(" - live from ")]
        if " - " in name and " remix" in name: name = name[:name.find(" - ")].strip() + " [Remix]"
        if " - " in name and " remaster" in name: name = name[:name.find(" - ")]
        variant = None
        if len(artists) <= 1: artists = "".join(artists)
        elif " (with" in name or not "(feat." in name:
            variant = artists[0]
            artists = " ".join(artists[:-2])+(" " if len(artists) > 2 else "")+artists[-2]+" & "+artists[-1]
            if " (with" in name: name = name[:name.find(" (with")]
        elif " (feat." in name:
            artists = artists[0]
            name = name[:name.find(" (feat.")]
        explicit = track['explicit']
        tracks[track['id']] = {"name":name.strip(), "explicit":explicit, "artist":artists.strip(), "variant":variant}
    return tracks

def get_clean_tracks(pid):
    tracks = get_playlist(pid)
    clean_tracks = set()
    profane_tracks = set()
    for t in tracks:
        if not tracks[t]["explicit"]:
            if not check_lyrics(url=make_genius_url(tracks[t]['artist'], tracks[t]['name']),
                                alt_url=make_genius_url(tracks[t]['variant'], tracks[t]['name']) if tracks[t]['variant'] else None):
                print(f"No profanity found for track ID {t}!")
                clean_tracks.add(t)
            else:
                print(f"Found profanity for track ID {t}!")
                profane_tracks.add(t)
        else:
            profane_tracks.add(t)
    return clean_tracks



get_clean_tracks("0nlqooedIJm8hyuhwa2X0M")