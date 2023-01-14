from utilities import get_token
import datetime
import json
import os
import random

spotify = get_token()

def get_library():
    with open("output.txt", "w+") as outf: 
        for i in range(8):
            albums = spotify.get(f"https://api.spotify.com/v1/me/albums?limit=50&offset={i * 50}").json()
            for alb in albums['items']:
                alb_name = alb['album']['name']
                alb_artist = " & ".join([art['name'] for art in alb['album']['artists']])
                alb_added = datetime.datetime.fromisoformat(alb['added_at'][:-1]).strftime("%B %d").replace(" 0", " ")
                outf.write(f'{alb_added} - {alb_name} by {alb_artist}\n')

def load_playlist():
    ts = set()
    for i in range(2):
        # heads up that the playlist endpoint doesn't support offset, only tracks does
        ts |= {t['track']['uri'] for t in spotify.get(f"https://api.spotify.com/v1/playlists/5Zh2ABcQAerLOj6884kIzX/tracks?offset={i * 100}&limit=100").json()['items']}
        
    tracks = list(ts)
    random.shuffle(tracks)
    for i in range(0, (len(tracks) // 100) + 1):
        spotify.post(f"https://api.spotify.com/v1/playlists/5Zh2ABcQAerLOj6884kIzX/tracks?uris={','.join((turi for turi in tracks[100 * i : 100 * (i + 1)] if turi))}")

def make_top_playlist():
    with open(os.path.join(os.path.dirname(__file__), "wrapped", "output.txt")) as sf:
        uris = [f'spotify:track:{l.split(" ")[0]}' for l in sf.readlines()]
    
    # created_playlist = spotify.post(
    #     "https://api.spotify.com/v1/users/6rcq1j21davq3yhbk1t0l5xnt/playlists",
    #     data=json.dumps({
    #         "name": "Grab-Bag Bangers",
    #         "public": True,
    #         "description": "My favorite track from each memorable album I listened to in 2022"
    #     })
    # ).json()
    for i in range(0, len(uris) // 100 + 1):
        spotify.post(f"https://api.spotify.com/v1/playlists/2E5XnluXSPNe6q85H4SPJA/tracks?uris={','.join((turi for turi in uris[100 * i : 100 * (i + 1)] if turi))}")

if __name__ == "__main__":
    load_playlist()
